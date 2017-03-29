from __future__ import print_function
from __future__ import unicode_literals

from collections import OrderedDict
import calendar
import io
import itertools
import socket
import threading

from contextlib import contextmanager
from ftplib import FTP
from ftplib import error_reply
from ftplib import error_perm
from ftplib import error_temp

from six import PY2
from six import text_type

from . import errors
from .base import FS
from .constants import DEFAULT_CHUNK_SIZE
from .enums import ResourceType
from .enums import Seek
from .info import Info
from .iotools import line_iterator
from .mode import Mode
from .path import abspath
from .path import basename
from .path import normpath
from .path import split
from . import _ftp_parse as ftp_parse


__all__ = ['FTPFS']


@contextmanager
def ftp_errors(fs, path=None):
    try:
        with fs._lock:
            yield
    except socket.error:
        raise errors.RemoteConnectionError(
            msg='unable to connect to {}'.format(fs.host)
        )
    except error_temp as e:
        if path is not None:
            raise errors.ResourceError(
                path,
                msg="ftp error on resource '{}' ({})".format(path, e)
            )
        else:
            raise errors.OperationFailed(msg='ftp error ({})'.format(e))
    except error_perm as e:
        code, message = parse_ftp_error(e)
        if code == 552:
            raise errors.InsufficientStorage(
                path=path,
                msg=message
            )
        elif code in (501, 550):
            raise errors.ResourceNotFound(path=path)
        raise errors.PermissionDenied(
            msg=message
        )


@contextmanager
def manage_ftp(ftp):
    try:
        yield ftp
    finally:
        try:
            ftp.quit()
        except:  # pragma: nocover
            pass

def parse_ftp_error(e):
    code, _, message = text_type(e).partition(' ')
    if code.isdigit():
        code = int(code)
    return code, message


def _encode(s):
    return s.encode() if PY2 and isinstance(s, text_type) else s


class FTPFile(object):

    def __init__(self, ftpfs, path, mode):
        self.fs = ftpfs
        self.path = path
        self.mode = Mode(mode)
        self.pos = 0
        self._lock = threading.Lock()
        self.ftp = self._open_ftp()
        self._read_conn = None
        self._write_conn = None
        self._closed = False

    def _open_ftp(self):
        ftp = self.fs._open_ftp()
        ftp.voidcmd(_encode('TYPE I'))
        return ftp

    @property
    def read_conn(self):
        if self._read_conn is None:
            self._read_conn = self.ftp.transfercmd(
                _encode('RETR ' + self.path),
                self.pos
            )
        return self._read_conn

    @property
    def write_conn(self):
        if self._write_conn is None:
            if self.mode.appending:
                self._write_conn = self.ftp.transfercmd(
                    _encode('APPE ' + self.path)
                )
            else:
                self._write_conn = self.ftp.transfercmd(
                    _encode('STOR ' + self.path),
                    self.pos
                )
        return self._write_conn

    def __repr__(self):
        _repr = "<ftpfile {!r} {!r} {!r}>"
        return _repr.format(self.fs.ftp_url, self.path, self.mode)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def __iter__(self):
        return line_iterator(self)

    def __del__(self):
        self.close()

    def flush(self):
        pass

    def next(self):
        return self.readline()

    __next__ = next

    def close(self):
        with self._lock:
            if not self._closed:
                try:
                    if self._write_conn is not None:
                        self._write_conn.close()
                        self._write_conn = None
                    if self._read_conn is not None:
                        self._read_conn.close()
                        self._read_conn = None
                    try:
                        self.ftp.quit()
                    except error_temp:  # pragma: nocover
                        pass
                finally:
                    self._closed = True

    def tell(self):
        return self.pos

    def read(self, size=None):
        if not self.mode.reading:
            raise IOError('File not open for reading')

        chunks = []
        remaining = size

        conn = self.read_conn
        with self._lock:
            while remaining is None or remaining:
                if remaining is None:
                    read_size = DEFAULT_CHUNK_SIZE
                else:
                    read_size = min(DEFAULT_CHUNK_SIZE, remaining)
                try:
                    chunk = conn.recv(read_size)
                except socket.error:  # pragma: nocover
                    break
                if not chunk:
                    break
                chunks.append(chunk)
                self.pos += len(chunk)
                if remaining is not None:
                    remaining -= len(chunk)
        return b''.join(chunks)

    def readline(self, size=None):
        return next(line_iterator(self, size))

    def readlines(self, hint=-1):
        lines = []
        size = 0
        for line in line_iterator(self):
            lines.append(line)
            size += len(line)
            if hint != -1 and size > hint:
                break
        return lines

    def write(self, data):
        if not self.mode.writing:
            raise IOError('File not open for writing')

        with self._lock:
            conn = self.write_conn
            data_pos = 0
            remaining_data = len(data)

            while remaining_data:
                chunk_size = min(remaining_data, DEFAULT_CHUNK_SIZE)
                sent_size = conn.send(data[data_pos:data_pos + chunk_size])
                data_pos += sent_size
                remaining_data -= sent_size
                self.pos += sent_size

    def writelines(self, lines):
        self.write(b''.join(lines))

    def truncate(self, size=None):
        # Inefficient, but I don't know if truncate is possible with ftp
        with self._lock:
            if size is None:
                size = self.tell()
            with self.fs.openbin(self.path) as f:
                data = f.read(size)
            with self.fs.openbin(self.path, 'w') as f:
                f.write(data)
                if len(data) < size:
                    f.write(b'\0' * (size - len(data)))


    def seek(self, pos, whence=Seek.set):
        if whence not in (Seek.set, Seek.current, Seek.end):
            raise ValueError('invalid value for whence')
        with self._lock:
            if whence == Seek.set:
                new_pos = pos
            elif whence == Seek.current:
                new_pos = self.pos + pos
            elif whence == Seek.end:
                file_size = self.fs.getsize(self.path)
                new_pos = file_size + pos
            self.pos = max(0, new_pos)

            self.ftp.quit()
            self.ftp = self._open_ftp()

            if self._read_conn:
                self._read_conn.close()
                self._read_conn = None
            if self._write_conn:
                self._write_conn.close()
                self._write_conn = None


class FTPFS(FS):
    """
    A FTP (File Transport Protocol) Filesystem.

    :param str host: A FTP host, e.g. ``'ftp.mirror.nl'``.
    :param str user: A username (default is ``'anonymous'``)
    :param passwd: Password for the server, or ``None`` for anon.
    :param acct: FTP account.
    :param int timeout: Timeout for contacting server (in seconds).
    :param int port: Port number (default 21).

    """

    _meta = {
        'case_insensitive': False,
        'invalid_path_chars': '\0',
        'network': True,
        'read_only': False,
        'thread_safe': True,
        'unicode_paths': True,
        'virtual': False,
    }

    def __init__(self,
                 host,
                 user='anonymous',
                 passwd='',
                 acct='',
                 timeout=10,
                 port=21):
        super(FTPFS, self).__init__()
        self.host = host
        self.user = user
        self.passwd = passwd
        self.acct = acct
        self.timeout = timeout
        self.port = port

        self._ftp = None
        self._welcome = None
        self._features = None

    def __repr__(self):
        return "FTPFS({!r}, port={!r})".format(self.host, self.port)

    def __str__(self):
        _fmt = (
            "<ftpfs '{host}'>"
            if self.port == 21
            else "<ftpfs '{host}:{port}'>"
        )
        return _fmt.format(host=self.host, port=self.port)

    def _open_ftp(self):
        _ftp = FTP()
        _ftp.set_debuglevel(0)
        with ftp_errors(self):
            _ftp.connect(self.host, self.port, self.timeout)
            _ftp.login(self.user, self.passwd, self.acct)
        return _ftp

    def _manage_ftp(self):
        ftp = self._open_ftp()
        return manage_ftp(ftp)

    @property
    def ftp_url(self):
        url = (
            "ftp://{}".format(self.host)
            if self.port == 21
            else "ftp://{}:{}".format(self.host, self.port)
        )
        return url

    @property
    def ftp(self):
        if self._ftp is None:
            self._ftp = self._open_ftp()
            self._welcome = self._ftp.getwelcome()
        return self._ftp

    @property
    def features(self):
        """Get features dict from FTP server."""
        if self._features is None:
            try:
                response = self.ftp.sendcmd(_encode("FEAT"))
            except error_perm:
                self._features = {}
            else:
                self._features = {}
                if PY2:
                    response = response.decode('ascii')
                if response.split('-')[0] == '211':
                    for line in response.splitlines():
                        if line.startswith(' '):
                            k, _, v = line[1:].partition(' ')
                            self._features[k] = v
        return self._features

    def _read_dir(self, path):
        _path = abspath(normpath(path))
        lines = []
        with ftp_errors(self, path=path):
            self.ftp.retrlines(
                _encode('LIST {}'.format(_path)),
                lines.append
            )
        lines = [
            line.decode('utf-8') if isinstance(line, bytes) else line
            for line in lines
        ]
        _list = [Info(raw_info) for raw_info in ftp_parse.parse(lines)]
        dir_listing = OrderedDict({info.name: info for info in _list})
        return dir_listing

    @property
    def supports_mlst(self):
        return 'MLST' in self.features

    def create(self, path, wipe=False):
        self.check()
        self.validatepath(path)
        with ftp_errors(self, path):
            if wipe or not self.isfile(path):
                empty_file = io.BytesIO()
                self.ftp.storbinary(
                    _encode("STOR {}".format(path)),
                    empty_file
                )

    @classmethod
    def _parse_ftp_time(cls, t):
        try:
            tm_year = int(t[0:4])
            tm_month = int(t[4:6])
            tm_day = int(t[6:8])
            tm_hour = int(t[8:10])
            tm_min = int(t[10:12])
            tm_sec = int(t[12:14])
        except ValueError:
            return None
        epoch_time = calendar.timegm((
            tm_year,
            tm_month,
            tm_day,
            tm_hour,
            tm_min,
            tm_sec
        ))
        return epoch_time

    @classmethod
    def _parse_facts(cls, line):
        name = None
        facts = {}
        for fact in line.split(';'):
            k, sep, v = fact.partition('=')
            if sep:
                k = k.strip().lower()
                v = v.strip()
                facts[k] = v
            else:
                name = basename(fact.rstrip('/').strip())
        return name if name not in ('.', '..') else None, facts

    @classmethod
    def _parse_mlsx(cls, lines):
        for line in lines:
            name, facts = cls._parse_facts(line.strip())
            if name is None:
                continue
            is_dir = facts.get('type', None) in ('dir', 'cdir', 'pdir')
            raw_info = {
                "basic":
                {
                    "name": name,
                    "is_dir": is_dir,
                },
                "details":
                {
                    "type": (
                        int(ResourceType.directory)
                        if is_dir else
                        int(ResourceType.file)
                    )
                },
                "ftp": facts
            }
            details = raw_info['details']
            size_str = facts.get('size', facts.get('sizd', '0'))
            size = 0
            if size_str.isdigit():
                size = int(size_str)
            details['size'] = size
            if 'modify' in facts:
                details['modified'] = cls._parse_ftp_time(facts['modify'])
            if 'create' in facts:
                details['created'] = cls._parse_ftp_time(facts['create'])
            yield raw_info

    def getinfo(self, path, namespaces=None):
        self.check()
        _path = self.validatepath(path)
        namespaces = namespaces or ()

        if _path == '/':
            return Info({
                "basic":
                {
                    "name": "",
                    "is_dir": True
                },
                "details":
                {
                    "type": int(ResourceType.directory)
                }
            })

        if self.supports_mlst:
            with self._lock:
                with ftp_errors(self, path=path):
                    response = self.ftp.sendcmd(
                        _encode('MLST {}'.format(_path))
                    )
                if PY2:
                    response = response.decode('utf-8')
                lines = response.splitlines()[1:-1]
                for raw_info in self._parse_mlsx(lines):
                    return Info(raw_info)

        with ftp_errors(self, path=path):
            dir_name, file_name = split(_path)
            directory = self._read_dir(dir_name)
            if file_name not in directory:
                raise errors.ResourceNotFound(path)
            info = directory[file_name]
            return info

    def listdir(self, path):
        self.check()
        _path = self.validatepath(path)
        with self._lock:
            dir_list = [
                info.name
                for info in self.scandir(_path)
            ]
        return dir_list

    def makedir(self, path, permissions=None, recreate=False):
        self.check()
        self.validatepath(path)
        _path = abspath(normpath(path))

        with ftp_errors(self, path=path):
            if _path == '/':
                if recreate:
                    return self.opendir(path)
                else:
                    raise errors.DirectoryExists(path)

            if not (recreate and self.isdir(path)):
                try:
                    self.ftp.mkd(_encode(_path))
                except error_perm as e:
                    code, _ = parse_ftp_error(e)
                    if code == 550:
                        if self.isdir(path):
                            raise errors.DirectoryExists(path)
                        else:
                            if self.exists(path):
                                raise errors.DirectoryExists(path)
                    raise errors.ResourceNotFound(path)
        return self.opendir(path)

    def openbin(self, path, mode="r", buffering=-1, **options):
        _mode = Mode(mode)
        _mode.validate_bin()
        self.check()
        self.validatepath(path)

        with self._lock:
            try:
                info = self.getinfo(path)
            except errors.ResourceNotFound:
                if _mode.reading:
                    raise errors.ResourceNotFound(path)
            else:
                if info.is_dir:
                    raise errors.FileExpected(path)
            if _mode.exclusive:
                raise errors.FileExists(path)
            f = FTPFile(self, abspath(normpath(path)), mode)
        return f

    def remove(self, path):
        self.check()
        self.validatepath(path)
        _path = abspath(normpath(path))
        dir_name, file_name = split(_path)
        with self._lock:
            if self.isdir(path):
                raise errors.FileExpected(path=path)
            with ftp_errors(self, path):
                self.ftp.delete(_encode(_path))

    def removedir(self, path):
        self.check()
        _path = abspath(normpath(path))
        self.validatepath(path)
        if _path == '/':
            raise errors.RemoveRootError()
        _dir_name, file_name = split(_path)

        with ftp_errors(self, path):
            try:
                self.ftp.rmd(_encode(_path))
            except error_perm as e:
                code, _ = parse_ftp_error(e)
                if code == 550:
                    if self.isfile(path):
                        raise errors.DirectoryExpected(path)
                    if not self.isempty(path):
                        raise errors.DirectoryNotEmpty(path)
                raise  # pragma: no cover

    def _scandir(self, path, namespaces=None):
        self.check()
        self.validatepath(path)
        _path = abspath(normpath(path))
        with self._lock:
            if self.supports_mlst:
                lines = []
                with ftp_errors(self, path=path):
                    try:
                        self.ftp.retrlines(
                            _encode("MLSD {}".format(_path)), lines.append
                        )
                    except error_perm as e:
                        if not self.getinfo(path).is_dir:
                            raise errors.DirectoryExpected(path)
                        raise # pragma: no cover
                if lines:
                    for raw_info in self._parse_mlsx(lines):
                        yield Info(raw_info)
                    return
            with self._lock:
                for info in self._read_dir(_path).values():
                    yield info

    def scandir(self, path, namespaces=None, page=None):
        if not self.supports_mlst and not self.getinfo(path).is_dir:
            raise errors.DirectoryExpected(path)
        iter_info = self._scandir(path, namespaces=namespaces)
        if page is not None:
            start, end = page
            iter_info = itertools.islice(iter_info, start, end)
        return iter_info

    def setbinfile(self, path, file):
        _path = abspath(normpath(path))
        self.validatepath(path)
        with self._lock:
            with self._manage_ftp() as ftp:
                with ftp_errors(self, path):
                    ftp.storbinary(
                        "STOR {}".format(_encode(_path)),
                        file
                    )

    def setbytes(self, path, contents):
        if not isinstance(contents, bytes):
            raise ValueError('contents must be bytes')
        _path = abspath(normpath(path))
        self.validatepath(path)
        bin_file = io.BytesIO(contents)
        with self._lock:
            with self._manage_ftp() as ftp:
                with ftp_errors(self, path):
                    ftp.storbinary(
                        "STOR {}".format(_encode(_path)),
                        bin_file
                    )

    def setinfo(self, path, info):
        if not self.exists(path):
            raise errors.ResourceNotFound(path)

    def getbytes(self, path):
        _path = abspath(normpath(path))
        data = io.BytesIO()
        with ftp_errors(self, path):
            with self._manage_ftp() as ftp:
                try:
                    ftp.retrbinary("RETR {}".format(_path), data.write)
                except error_perm as e:
                    code, _ = parse_ftp_error(e)
                    if code == 550:
                        if self.isdir(path):
                            raise errors.FileExpected(path)
                    raise

        data_bytes = data.getvalue()
        return data_bytes

    def close(self):
        if not self.isclosed():
            try:
                self.ftp.quit()
            except Exception:
                pass
            self._ftp = None
        super(FTPFS, self).close()


if __name__ == "__main__":  # pragma: no cover
    fs = FTPFS('ftp.mirror.nl', 'anonymous', 'willmcgugan@gmail.com')
    print(list(fs.scandir('/')))
