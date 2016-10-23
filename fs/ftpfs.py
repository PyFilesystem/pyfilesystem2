from __future__ import print_function
from __future__ import unicode_literals

from contextlib import contextmanager
from ftplib import FTP, error_perm, error_temp
import io
import socket
import threading

from six import text_type, PY2

from .base import FS
from .enums import ResourceType, Seek
from .constants import DEFAULT_CHUNK_SIZE
from .mode import validate_openbin_mode
from .info import Info
from .iotools import line_iterator
from .path import abspath, normpath, split
from . import errors
from ._ftp_parse import FTPListDataParser


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
        raise errors.RemoteConnectionError(
            msg='ftp error ({})'.format(e)
        )
    except error_perm as e:
        code, message = parse_ftp_error(e)
        if code == 552:
            raise errors.InsufficientStorage(
                path=path,
                msg=message
            )
        elif code == 550:
            raise errors.ResourceNotFound(path=path)
        raise errors.PermissionDenied(
            msg=message
        )


def parse_ftp_error(e):
    code, _, message = text_type(e).partition(' ')
    if code.isdigit():
        code = int(code)
    return code, _decode(message)


def _encode(s):
    if PY2 and isinstance(s, text_type):
        return s.encode('utf-8')
    return s


def _decode(s):
    if isinstance(s, bytes):
        return s.decode('utf-8')
    return s


class FTPFile(object):
    """
    A binary file object for an ftp file.

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
            self.pos = self.fs.getsize(self.path)

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
            if self._socket is not None:
                try:
                    self._socket.close()
                except:
                    pass
            try:
                self.ftp.quit()
            except:
                pass
            self.closed = True

    def flush(self):
        pass

    def next(self):
        return self.readline()

    __next__ = next

    def readline(self, size=None):
        return next(line_iterator(self, size))

    def readlines(self, hint=-1):
        if hint == -1:
            return list(line_iterator(self))
        lines = []
        size = 0
        for line in line_iterator(self):
            lines.append(line)
            size += len(line)
            if size > hint:
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
                sock.close()
                ftp.voidresp()

    def seek(self, pos, whence=Seek.set):
        if whence == Seek.set:
            self.pos = pos
        elif whence == Seek.current:
            self.pos = self.pos + pos
        elif whence == Seek.end:
            self.pos = max(0, self.fs.getsize(self.path) - pos)
        else:
            raise ValueError('invalid value for seek')

    def seekable(self):
        return True

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
                    f.write(b'\0' * size - len(data))

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

    _meta = {
        'case_insensitive': False,
        'invalid_path_chars': '\0',
        'network': True,
        'read_only': False,
        'thread_safe': True,
        'unicode_paths': True,
        'virtual': False,
    }

    def __init__(self, host,
                 user='', passwd='', acct='', timeout=None, port=21):
        super(FTPFS, self).__init__()
        self.host = host
        self.user = user
        self.passwd = passwd
        self.acct = acct
        self.timeout = None
        self.port = port

        self._ftp = None
        self._welcome = None

    def __repr__(self):
        return "FTPFS({!r}, port={!r})".format(self.host, self.port)

    def __str__(self):
        return "<ftpfps '{}:{}'>".format(self.host, self.port)

    def _open_ftp(self):
        _ftp = FTP()
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

    def _read_dir(self, path):
        _path = abspath(normpath(path))
        with self._lock:
            ftp = self.ftp
            lines = []

            with ftp_errors(self, path):
                try:
                    ftp.dir(_encode(_path), lines.append)
                except error_perm as e:
                    code, _ = parse_ftp_error(e)
                    if code == 550 and not self.getbasic(path).is_dir:
                        raise errors.DirectoryExpected(path)
                    raise

            parser = FTPListDataParser()
            entries = [parser.parse_line(line) for line in lines]
            return entries

    @classmethod
    def _make_raw_info(cls, entry):
        is_dir = entry.try_cwd
        resource_type = int(
            ResourceType.directory
            if is_dir
            else ResourceType.file
        )
        raw_info = {
            "basic": {
                "name": _decode(entry.name),
                "is_dir": is_dir
            },
            "details": {
                "modified": entry.mtime,
                "size": entry.size,
                "type": resource_type
            }
        }
        raw_info['ftp'] = {
            k: getattr(entry, k)
            for k in dir(entry)
            if not k.startswith('_')
        }
        return raw_info

    def create(self, path, wipe=False):
        self._check()
        self.validatepath(path)
        with ftp_errors(self, path):
            if wipe or not self.isfile(path):
                empty_file = io.BytesIO()
                self.ftp.storbinary(
                    _encode("STOR {}".format(path)),
                    empty_file
                )

    def getinfo(self, path, namespaces=None):
        self._check()
        self.validatepath(path)
        namespaces = namespaces or ()
        _path = abspath(normpath(path))
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

        dir_path, file_name = split(_path)

        with self._lock:
            ftp = self.ftp
            lines = []

            with ftp_errors(self, path):
                ftp.dir(_encode(dir_path), lines.append)

            parser = FTPListDataParser()
            entries = [parser.parse_line(line) for line in lines]

        for entry in entries:
            if entry.name == file_name:
                break
        else:
            raise errors.ResourceNotFound(path)

        raw_info = self._make_raw_info(entry)
        return Info(raw_info)

    def exists(self, path):
        _path = abspath(normpath(path))
        try:
            self.ftp.dir(_encode(_path), lambda line: None)
        except error_perm:
            return False
        else:
            return True

    def isdir(self, path):
        _path = abspath(normpath(path))
        try:
            self.ftp.cwd(_encode(_path))
        except error_perm:
            return False
        else:
            return True

    def isfile(self, path):
        _path = abspath(normpath(path))
        try:
            self.ftp.cwd(_encode(_path))
        except error_perm:
            return self.exists(path)
        else:
            return False

    def listdir(self, path):
        self._check()
        _path = abspath(normpath(path))
        with self._lock:
            if not self.getbasic(path).is_dir:
                raise errors.DirectoryExpected(path)
            entries = self._read_dir(_path)
        dir_list = [_decode(entry.name) for entry in entries]
        return dir_list

    def makedir(self, path, permissions=None, recreate=False):
        self._check()
        self.validatepath(path)
        _path = abspath(normpath(path))

        with ftp_errors(self, path=path):
            if _path == '/':
                if recreate:
                    return self.opendir(path)
                else:
                    raise errors.DirectoryExists(path)

            if recreate and self.isdir(path):
                return self.opendir(path)
            try:
                self.ftp.mkd(_encode(_path))
            except error_perm as e:
                code, _ = parse_ftp_error(e)
                if code == 550:
                    if self.isdir(path):
                        if recreate:
                            return self.opendir(path)
                        else:
                            raise errors.DirectoryExists(path)
                    else:
                        if self.exists(path):
                            raise errors.DirectoryExpected(path)
                    raise errors.ResourceNotFound(path)
                raise
        return self.opendir(path)

    def openbin(self, path, mode="r", buffering=-1, **options):
        validate_openbin_mode(mode)
        self._check()
        self.validatepath(path)
        mode = mode.lower()

        with self._lock:
            try:
                info = self.getinfo(path)
            except errors.ResourceNotFound:
                if 'r' in mode or 'a' in mode:
                    raise errors.ResourceNotFound(path)
            else:
                if info.is_dir:
                    raise errors.FileExpected(path)
            f = FTPFile(self, abspath(normpath(path)), mode)
        return f

    def remove(self, path):
        self._check()
        self.validatepath(path)
        _path = abspath(normpath(path))
        dir_name, file_name = split(_path)
        with self._lock:
            if self.isdir(path):
                raise errors.DirectoryExpected(path=path)
            with ftp_errors(self, path):
                self.ftp.delete(_encode(_path))

    def removedir(self, path):
        self._check()
        _path = abspath(normpath(path))
        self.validatepath(path)
        if _path == '/':
            raise errors.RemoveRootError()
        dir_name, file_name = split(_path)
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
                raise

    def scandir(self, path, namespaces=None):
        self._check()
        self.validatepath(path)
        _path = abspath(normpath(path))
        with self._lock:
            if not self.getbasic(path).is_dir:
                raise errors.DirectoryExpected(path)
            entries = self._read_dir(_path)
        for entry in entries:
            raw_info = self._make_raw_info(entry)
            yield Info(raw_info)

    def setbin(self, path, file):
        _path = abspath(normpath(path))
        self.validatepath(path)
        with self._lock:
            with ftp_errors(self, path):
                self.ftp.storbinary(
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
            with ftp_errors(self, path):
                self.ftp.storbinary(
                    "STOR {}".format(_encode(_path)),
                    bin_file
                )

    def getbytes(self, path):
        _path = abspath(normpath(path))
        data = io.BytesIO()
        with ftp_errors(self, path):
            try:
                self.ftp.retrbinary("RETR {}".format(_path), data.write)
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
            except:
                pass
        super(FTPFS, self).close()


if __name__ == "__main__":
    ftp_fs = FTPFS('127.0.0.1', port=2121)
    ftp_fs.openbin('new.txt', 'w').write(b'test')
    #print(list(ftp_fs.scandir('foobar')))
    ftp_fs.makedirs('/foo/baz', recreate=True)
    print(ftp_fs.isfile('test.txt'))
    print(ftp_fs.isdir('test.txt'))
    print(ftp_fs.isdir('foo'))
    print(ftp_fs.isfile('foo'))
    print(ftp_fs.isdir('nope'))
    print(ftp_fs.isfile('nope'))
    print(ftp_fs.getinfo('test.txt').raw)
    print(ftp_fs.getinfo('foo').raw)
    print(dir(ftp_fs._read_dir('test.txt')[0]))


    # print(ftp_fs.listdir('/'))
    # ftp_fs.makedirs('foo/bar/', recreate=True)
    # ftp_fs.setbytes('foo/bar/test.txt', b'hello')

    # f = ftp_fs.openbin('foo/bar/test.txt')
    # print(f.read(3))
    # print(f.read(3))
    # print(ftp_fs.listdir('foo/bar/test.txt'))