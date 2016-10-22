from __future__ import print_function
from __future__ import unicode_literals

from contextlib import contextmanager
from ftplib import FTP, error_perm, error_temp, error_proto, error_reply
import io
import socket
import threading

from six import text_type

from .base import FS
from .enums import ResourceType, Seek
from .constants import DEFAULT_CHUNK_SIZE
from .mode import validate_openbin_mode
from .info import Info
from .iotools import line_iterator
from .path import abspath, dirname, normpath, relpath, split
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
        print("FTP ERROR {}".format(e))
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
    return code, message.decode('utf-8')


def _encode(s):
    if isinstance(s, text_type):
        return s.encode('utf-8')
    return s


def _decode(s):
    if isinstance(s, bytes):
        return s.decode('utf-8')
    return s


class _FTPFile(object):
    """ A file-like that provides access to a file being streamed over ftp."""

    def __init__(self, ftpfs, path, mode):
        self.fs = ftpfs
        self.path = path
        self.mode = mode

        self._lock = threading.RLock()
        self.ftp = ftpfs._open_ftp()
        self.read_pos = 0

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def read(self, size=None):
        with self._lock:
            if size is None:
                data_file = io.BytesIO()
                self.ftp.retrbinary(
                    _encode('RETR {}'.format(self.path)),
                    data_file.write,
                    rest=self.read_pos
                )
                data_bytes = data_file.getvalue()
                self.read_pos += len(data_bytes)
                return data_bytes
            else:
                data_file = io.BytesIO()
                bytes_remaining = size
                self.ftp.voidcmd(_encode('TYPE I'))
                conn = self.ftp.transfercmd(
                    _encode('RETR {}'.format(self.path)),
                    self.read_pos
                )
                try:
                    while bytes_remaining:
                        chunk_bytes = conn.recv(
                            min(DEFAULT_CHUNK_SIZE, bytes_remaining)
                        )
                        if not chunk_bytes:
                            break
                        data_file.write(chunk_bytes)
                        self.read_pos += len(chunk_bytes)
                        bytes_remaining -= len(chunk_bytes)
                    data_bytes = data_file.getvalue()
                    return data_bytes
                finally:
                    conn.close()
                    self.ftp.voidresp()

    def close(self):
        try:
            self.ftp.quit()
        except:
            pass




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
                    if code == 550 and self.isfile(path):
                        raise errors.DirectoryExpected(path)
                    raise

            entries = []
            parser = FTPListDataParser()
            for line in lines:
                entry = parser.parse_line(line)
                entries.append(entry)
            return entries

    @classmethod
    def _make_raw_info(cls, entry):
        is_dir = entry.try_cwd
        resource_type = (
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

        dir_path, resource_name = split(_path)
        entries = self._read_dir(dir_path)

        for entry in entries:
            if entry.name == resource_name:
                break
        else:
            raise errors.ResourceNotFound(path)

        raw_info = self._make_raw_info(entry)
        return Info(raw_info)

    def listdir(self, path):
        self._check()
        _path = abspath(normpath(path))
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

            try:
                self.ftp.mkd(_encode(relpath(_path)))
            except error_reply as e:
                pass
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
            if self.isdir(path):
                raise errors.FileExpected(path)
            if 'r' in mode or 'a' in mode:
                if not self.isfile(path):
                    raise errors.ResourceNotFound(path)
            f = _FTPFile(self, normpath(path), mode)
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
                self.ftp.delete(_encode(path))

    def removedir(self, path):
        self._check()
        _path = abspath(normpath(path))
        self.validatepath(path)
        if _path == '/':
            raise errors.RemoveRootError()
        dir_name, file_name = split(_path)
        with ftp_errors(self, path):
            try:
                self.ftp.rmd(_encode(path))
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
        entries = self._read_dir(_path)
        for entry in entries:
            raw_info = self._make_raw_info(entry)
            yield Info(raw_info)

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
                    info = self.getinfo(path)
                    if not self.isdir(dirname(path)):
                        raise errors.DirectoryExpected(path)
                    if info.is_dir:
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
    print(ftp_fs.listdir('/'))
    ftp_fs.makedirs('foo/bar/', recreate=True)
    ftp_fs.setbytes('foo/bar/test.txt', b'hello')

    f = ftp_fs.openbin('foo/bar/test.txt')
    print(f.read(3))
    print(f.read(3))