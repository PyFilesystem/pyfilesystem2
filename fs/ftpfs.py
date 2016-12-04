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


def parse_ftp_error(e):
    code, _, message = text_type(e).partition(' ')
    if code.isdigit():
        code = int(code)
    return code, message


def _encode(s):
    return s.encode() if PY2 and isinstance(s, text_type) else s


class FTPFile(object):
    """
    A binary file object for an ftp file.

    You won't need to create these manually. They will be returned by
    ``FTPFS`` objects when you open a file.

    """

    def __init__(self, ftpfs, path, mode):
        self.fs = ftpfs
        self.path = path
        self.mode = mode

        self._lock = threading.RLock()
        self.ftp = ftpfs._open_ftp()
        self.ftp.voidcmd(_encode('TYPE I'))
        self.pos = 0
        self._socket = None
        self.closed = False


        if 'a' in mode:
            try:
                self.pos = self.fs.getsize(self.path)
            except errors.ResourceNotFound:
                self.pos = 0

    def __repr__(self):
        _repr = "FTPFile({!r}, {!r}, {!r})"
        return _repr.format(self.fs, self.path, self.mode)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def __iter__(self):
        return line_iterator(self)

    def close(self):
        if not self.closed:
            self.ftp.quit()
            self.closed = True

    def flush(self):
        pass

    def next(self):
        return self.readline()

    __next__ = next

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

    def read(self, size=None):
        with self._lock:
            ftp = self.ftp
            data_file = io.BytesIO()
            bytes_remaining = size

            sock = self.ftp.transfercmd(
                _encode('RETR {}'.format(self.path)),
                self.pos
            )
            try:
                while 1:
                    chunk_size = (
                        DEFAULT_CHUNK_SIZE
                        if size is None
                        else
                        min(DEFAULT_CHUNK_SIZE, bytes_remaining)
                    )
                    chunk_bytes = sock.recv(chunk_size)
                    if not chunk_bytes:
                        break
                    data_file.write(chunk_bytes)
                    self.pos += len(chunk_bytes)
                    if bytes_remaining is not None:
                        bytes_remaining -= len(chunk_bytes)
                        if not bytes_remaining:
                            break
                data_bytes = data_file.getvalue()
                return data_bytes
            finally:
                ftp.voidresp()
                sock.close()

    def seek(self, pos, whence=Seek.set):
        if whence == Seek.set:
            self.pos = pos
        elif whence == Seek.current:
            self.pos = self.pos + pos
        elif whence == Seek.end:
            self.pos = max(0, self.fs.getsize(self.path) + pos)
        else:
            raise ValueError('invalid value for whence')

    def tell(self):
        return self.pos

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

    def write(self, data):

        def on_write(chunk):
            self.pos += len(chunk)

        data_file = io.BytesIO(data)
        with ftp_errors(self.fs, self.path):
            self.ftp.storbinary(
                _encode('STOR {}'.format(self.path)),
                data_file,
                DEFAULT_CHUNK_SIZE,
                on_write,
                self.pos or None
            )

    def writelines(self, lines):
        self.write(b''.join(lines))


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
        #_ftp.set_debuglevel(2)
        with ftp_errors(self):
            _ftp.connect(self.host, self.port, self.timeout)
            _ftp.login(self.user, self.passwd, self.acct)
        return _ftp

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
            name, facts = cls._parse_facts(line)
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
                lines = [
                    line[1:]
                    for line in response.splitlines()
                    if line.startswith(' ')
                ]
                for raw_info in self._parse_mlsx(lines):
                    break
            return Info(raw_info)
        else:
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
                raise errors.DirectoryExpected(path=path)
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
                for raw_info in self._parse_mlsx(lines):
                    yield Info(raw_info)
            else:
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
            ftp = self._open_ftp()
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
            ftp = self._open_ftp()
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
            ftp = self._open_ftp()
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
        super(FTPFS, self).close()


if __name__ == "__main__":  # pragma: no cover
    fs = FTPFS('ftp.mirror.nl', 'anonymous', 'willmcgugan@gmail.com')
    print(list(fs.scandir('/')))
