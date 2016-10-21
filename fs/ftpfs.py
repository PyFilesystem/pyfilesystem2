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

    blocksize = 1024 * 64

    def __init__(self, ftpfs, ftp, path, mode):
        self._lock = threading.RLock()
        self.fs = ftpfs
        self.ftp = ftp
        self.path = normpath(path)
        self.mode = mode
        self.read_pos = 0
        self.write_pos = 0
        self.closed = False
        self.file_size = None
        if 'r' in mode or 'a' in mode:
            self.file_size = ftpfs.getsize(path)
        self.conn = None

        self._start_file(mode, _encode(self.path))

    def _reset(self):
        self.read_pos = 0
        self.write_pos = 0
        self.closed = False

    def _start_file(self, mode, path):
        with self._lock:
            with ftp_errors(self.fs):
                self.read_pos = 0
                self.write_pos = 0
                if 'r' in mode:
                    self.ftp.voidcmd(_encode('TYPE I'))
                    self.conn = self.ftp.transfercmd(_encode('RETR ' + path), None)

                else:#if 'w' in mode or 'a' in mode:
                    self.ftp.voidcmd(_encode('TYPE I'))
                    if 'a' in mode:
                        self.write_pos = self.file_size
                        self.conn = self.ftp.transfercmd(_encode('APPE ' + path))
                    else:
                        self.conn = self.ftp.transfercmd(_encode('STOR ' + path))

    def read(self, size=None):
        with self._lock:
            with ftp_errors(self.fs):
                if self.conn is None:
                    return b''

                chunks = []
                if size is None or size < 0:
                    while 1:
                        data = self.conn.recv(self.blocksize)
                        if not data:
                            self.conn.close()
                            self.conn = None
                            self.ftp.voidresp()
                            break
                        chunks.append(data)
                        self.read_pos += len(data)
                    return b''.join(chunks)

                remaining_bytes = size
                while remaining_bytes:
                    read_size = min(remaining_bytes, self.blocksize)
                    data = self.conn.recv(read_size)
                    if not data:
                        self.conn.close()
                        self.conn = None
                        self.ftp.voidresp()
                        break
                    chunks.append(data)
                    self.read_pos += len(data)
                    remaining_bytes -= len(data)

                return b''.join(chunks)

    def write(self, data):
        with self._lock:
            with ftp_errors(self.fs):
                data_pos = 0
                remaining_data = len(data)
                while remaining_data:
                    chunk_size = min(remaining_data, self.blocksize)
                    self.conn.sendall(data[data_pos:data_pos + chunk_size])
                    data_pos += chunk_size
                    remaining_data -= chunk_size
                    self.write_pos += chunk_size

    def writelines(self, lines):
        with self._lock:
            for data in lines:
                self.write(data)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def flush(self):
        pass

    def seek(self, pos, where=Seek.set):
        # Ftp doesn't support a real seek, so we close the transfer and resume
        # it at the new position with the REST command
        # I'm not sure how reliable this method is!
        if 'r' not in self.mode:
            raise IOError("Seek only works with files open for read")

        with ftp_errors(self.fs):
            with self._lock:
                current = self.tell()
                new_pos = None
                if where == Seek.set:
                    new_pos = pos
                elif where == Seek.current:
                    new_pos = current + pos
                elif where == Seek.end:
                    new_pos = self.file_size - pos
                if new_pos < 0:
                    raise ValueError("Can't seek before start of file")

                if self.conn is not None:
                    self.conn.close()

                self.close()

                self.ftp = self.fs._open_ftp()
                self.ftp.sendcmd(_encode('TYPE I'))
                self.ftp.sendcmd(_encode('REST {}'.format(new_pos)))
                self.read_pos = new_pos

    def tell(self):
        return self.read_pos if 'r' in self.mode else self.write_pos

    def truncate(self, size=None):
        with ftp_errors(self.fs):
            with self._lock:
                # Inefficient, but I don't know how else to implement this
                if size is None:
                    size = self.tell()

                if self.conn is not None:
                    self.conn.close()
                self.close()

                read_f = None
                try:
                    read_f = self.fs.open(self.path, 'rb')
                    data = read_f.read(size)
                finally:
                    if read_f is not None:
                        read_f.close()

                self.ftp = self.ftpfs._open_ftp()
                self.mode = 'w'
                # self.__init__(self.ftpfs, self.ftp, _encode(self.path), self.mode)
                self._start_file(self.mode, self.path)
                self.write(data)
                if len(data) < size:
                    self.write('\0' * (size - len(data)))

    def close(self):
        if self.conn is not None:
            try:
                self.conn.close()
                self.conn = None
                self.ftp.voidresp()
            except error_temp, error_perm:
                pass
        if self.ftp is not None:
            try:
                self.ftp.close()
            except error_temp, error_perm:
                pass
        self.closed = True

    def next(self):
        return self.readline()

    def readline(self, size=None):
        return next(line_iterator(self, size))

    def __iter__(self):
        return line_iterator(self)


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

    def getinfo(self, path, *namespaces):
        self._check()
        self.validatepath(path)
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
        print("makedir", _path)

        with ftp_errors(self, path=path):
            if _path == '/':
                if recreate:
                    return self.opendir(path)
                else:
                    raise errors.DirectoryExists(path)

            try:
                self.ftp.mkd(_encode(relpath(_path)))
            except error_reply as e:
                print("error_reply", e)
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
                        if not self.isdir(dirname(path)):
                            raise errors.ParentDirectoryMissing(path)
                    #raise errors.ResourceNotFound(path)
                raise
        return self.opendir(path)

    def openbin(self, path, mode="r", buffering=-1, **options):
        validate_openbin_mode(mode)
        self._check()
        self.validatepath(path)
        _path = abspath(normpath(path))
        mode = mode.lower()

        with self._lock:
            if self.isdir(path):
                raise errors.FileExpected(path)
            if 'r' in mode or 'a' in mode:
                if not self.isfile(path):
                    raise errors.ResourceNotFound(path)
            ftp = self._open_ftp()
        f = _FTPFile(self, ftp, normpath(path), mode)
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
            ftp = self._open_ftp()
            with ftp_errors(self, path):
                ftp.storbinary(
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


if __name__ == "__main__":
    ftp_fs = FTPFS('127.0.0.1', port=2121)
    print(ftp_fs.listdir('/'))
    ftp_fs.makedirs('foo/bar/', recreate=True)
    ftp_fs.setbytes('foo/bar/test.txt', b'hello')

