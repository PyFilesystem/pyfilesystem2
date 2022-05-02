"""Manage filesystems on remote FTP servers.
"""

from __future__ import print_function, unicode_literals

import typing

import array
import calendar
import datetime
import io
import itertools
import socket
import threading
from collections import OrderedDict
from contextlib import contextmanager
from ftplib import FTP

try:
    from ftplib import FTP_TLS
except ImportError as err:
    FTP_TLS = err  # type: ignore
from typing import cast

from ftplib import error_perm, error_temp
from six import PY2, raise_from, text_type

from . import _ftp_parse as ftp_parse
from . import errors
from .base import FS
from .constants import DEFAULT_CHUNK_SIZE
from .enums import ResourceType, Seek
from .info import Info
from .iotools import line_iterator
from .mode import Mode
from .path import abspath, basename, dirname, normpath, split
from .time import epoch_to_datetime

if typing.TYPE_CHECKING:
    from typing import (
        Any,
        BinaryIO,
        ByteString,
        Container,
        ContextManager,
        Dict,
        Iterable,
        Iterator,
        List,
        Optional,
        SupportsInt,
        Text,
        Tuple,
        Union,
    )

    import ftplib
    import mmap

    from .base import _OpendirFactory
    from .info import RawInfo
    from .permissions import Permissions
    from .subfs import SubFS


_F = typing.TypeVar("_F", bound="FTPFS")


__all__ = ["FTPFS"]


@contextmanager
def ftp_errors(fs, path=None):
    # type: (FTPFS, Optional[Text]) -> Iterator[None]
    try:
        with fs._lock:
            yield
    except socket.error:
        raise errors.RemoteConnectionError(
            msg="unable to connect to {}".format(fs.host)
        )
    except EOFError:
        raise errors.RemoteConnectionError(msg="lost connection to {}".format(fs.host))
    except error_temp as error:
        if path is not None:
            raise errors.ResourceError(
                path, msg="ftp error on resource '{}' ({})".format(path, error)
            )
        else:
            raise errors.OperationFailed(msg="ftp error ({})".format(error))
    except error_perm as error:
        code, message = _parse_ftp_error(error)
        if code == "552":
            raise errors.InsufficientStorage(path=path, msg=message)
        elif code in ("501", "550"):
            raise errors.ResourceNotFound(path=cast(str, path))
        raise errors.PermissionDenied(msg=message)


@contextmanager
def manage_ftp(ftp):
    # type: (FTP) -> Iterator[FTP]
    try:
        yield ftp
    finally:
        try:
            ftp.quit()
        except Exception:  # pragma: no cover
            pass


def _parse_ftp_error(error):
    # type: (ftplib.Error) -> Tuple[Text, Text]
    """Extract code and message from ftp error."""
    code, _, message = text_type(error).partition(" ")
    return code, message


if PY2:

    def _encode(st, encoding):
        # type: (Union[Text, bytes], Text) -> str
        return st.encode(encoding) if isinstance(st, text_type) else st

    def _decode(st, encoding):
        # type: (Union[Text, bytes], Text) -> Text
        return st.decode(encoding, "replace") if isinstance(st, bytes) else st

else:

    def _encode(st, _):
        # type: (str, str) -> str
        return st

    def _decode(st, _):
        # type: (str, str) -> str
        return st


class FTPFile(io.RawIOBase):
    def __init__(self, ftpfs, path, mode):
        # type: (FTPFS, Text, Text) -> None
        super(FTPFile, self).__init__()
        self.fs = ftpfs
        self.path = path
        self.mode = Mode(mode)
        self.pos = 0
        self._lock = threading.Lock()
        self.ftp = self._open_ftp()
        self._read_conn = None  # type: Optional[socket.socket]
        self._write_conn = None  # type: Optional[socket.socket]

    def _open_ftp(self):
        # type: () -> FTP
        """Open an ftp object for the file."""
        ftp = self.fs._open_ftp()
        ftp.voidcmd(str("TYPE I"))
        return ftp

    @property
    def read_conn(self):
        # type: () -> socket.socket
        if self._read_conn is None:
            self._read_conn = self.ftp.transfercmd(
                str("RETR ") + _encode(self.path, self.ftp.encoding), self.pos
            )
        return self._read_conn

    @property
    def write_conn(self):
        # type: () -> socket.socket
        if self._write_conn is None:
            if self.mode.appending:
                self._write_conn = self.ftp.transfercmd(
                    str("APPE ") + _encode(self.path, self.ftp.encoding)
                )
            else:
                self._write_conn = self.ftp.transfercmd(
                    str("STOR ") + _encode(self.path, self.ftp.encoding), self.pos
                )
        return self._write_conn

    def __repr__(self):
        # type: () -> str
        _repr = "<ftpfile {!r} {!r} {!r}>"
        return _repr.format(self.fs.ftp_url, self.path, self.mode)

    def close(self):
        # type: () -> None
        if not self.closed:
            with self._lock:
                try:
                    if self._write_conn is not None:
                        self._write_conn.close()
                        self._write_conn = None
                        self.ftp.voidresp()  # Ensure last write completed
                    if self._read_conn is not None:
                        self._read_conn.close()
                        self._read_conn = None
                    try:
                        self.ftp.quit()
                    except error_temp:  # pragma: no cover
                        pass
                finally:
                    super(FTPFile, self).close()

    def tell(self):
        # type: () -> int
        return self.pos

    def readable(self):
        # type: () -> bool
        return self.mode.reading

    def read(self, size=-1):
        # type: (int) -> bytes
        if not self.mode.reading:
            raise IOError("File not open for reading")

        chunks = []
        remaining = size

        conn = self.read_conn
        with self._lock:
            while remaining:
                if remaining < 0:
                    read_size = DEFAULT_CHUNK_SIZE
                else:
                    read_size = min(DEFAULT_CHUNK_SIZE, remaining)
                try:
                    chunk = conn.recv(read_size)
                except socket.error:  # pragma: no cover
                    break
                if not chunk:
                    break
                chunks.append(chunk)
                self.pos += len(chunk)
                remaining -= len(chunk)
        return b"".join(chunks)

    def readinto(self, buffer):
        # type: (Union[bytearray, memoryview, array.array[Any], mmap.mmap]) -> int
        data = self.read(len(buffer))
        bytes_read = len(data)
        if isinstance(buffer, array.array):
            buffer[:bytes_read] = array.array(buffer.typecode, data)
        else:
            buffer[:bytes_read] = data  # type: ignore
        return bytes_read

    def readline(self, size=None):
        # type: (Optional[int]) -> bytes
        return next(line_iterator(self, size))  # type: ignore

    def readlines(self, hint=-1):
        # type: (int) -> List[bytes]
        lines = []
        size = 0
        for line in line_iterator(self):  # type: ignore
            lines.append(line)
            size += len(line)
            if hint != -1 and size > hint:
                break
        return lines

    def writable(self):
        # type: () -> bool
        return self.mode.writing

    def write(self, data):
        # type: (Union[bytes, memoryview, array.array[Any], mmap.mmap]) -> int
        if not self.mode.writing:
            raise IOError("File not open for writing")

        if isinstance(data, array.array):
            data = data.tobytes()

        with self._lock:
            conn = self.write_conn
            data_pos = 0
            remaining_data = len(data)

            while remaining_data:
                chunk_size = min(remaining_data, DEFAULT_CHUNK_SIZE)
                sent_size = conn.send(data[data_pos : data_pos + chunk_size])
                data_pos += sent_size
                remaining_data -= sent_size
                self.pos += sent_size

        return data_pos

    def writelines(self, lines):
        # type: (Iterable[Union[bytes, memoryview, array.array[Any], mmap.mmap]]) -> None  # noqa: E501
        if not self.mode.writing:
            raise IOError("File not open for writing")
        data = bytearray()
        for line in lines:
            if isinstance(line, array.array):
                data.extend(line.tobytes())
            else:
                data.extend(line)  # type: ignore
        self.write(data)

    def truncate(self, size=None):
        # type: (Optional[int]) -> int
        # Inefficient, but I don't know if truncate is possible with ftp
        with self._lock:
            if size is None:
                size = self.tell()
            with self.fs.openbin(self.path) as f:
                data = f.read(size)
            with self.fs.openbin(self.path, "w") as f:
                f.write(data)
                if len(data) < size:
                    f.write(b"\0" * (size - len(data)))
        return size

    def seekable(self):
        # type: () -> bool
        return True

    def seek(self, pos, whence=Seek.set):
        # type: (int, SupportsInt) -> int
        _whence = int(whence)
        if _whence not in (Seek.set, Seek.current, Seek.end):
            raise ValueError("invalid value for whence")
        with self._lock:
            if _whence == Seek.set:
                new_pos = pos
            elif _whence == Seek.current:
                new_pos = self.pos + pos
            elif _whence == Seek.end:
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
        return self.tell()


class FTPFS(FS):
    """A FTP (File Transport Protocol) Filesystem.

    Optionally, the connection can be made securely via TLS. This is known as
    FTPS, or FTP Secure. TLS will be enabled when using the ftps:// protocol,
    or when setting the `tls` argument to True in the constructor.

    Examples:
        Create with the constructor::

            >>> from fs.ftpfs import FTPFS
            >>> ftp_fs = FTPFS("demo.wftpserver.com")

        Or via an FS URL::

            >>> ftp_fs = fs.open_fs('ftp://test.rebex.net')

        Or via an FS URL, using TLS::

            >>> ftp_fs = fs.open_fs('ftps://demo.wftpserver.com')

        You can also use a non-anonymous username, and optionally a
        password, even within a FS URL::

            >>> ftp_fs = FTPFS("test.rebex.net", user="demo", passwd="password")
            >>> ftp_fs = fs.open_fs('ftp://demo:password@test.rebex.net')

        Connecting via a proxy is supported. If using a FS URL, the proxy
        URL will need to be added as a URL parameter::

            >>> ftp_fs = FTPFS("ftp.ebi.ac.uk", proxy="test.rebex.net")
            >>> ftp_fs = fs.open_fs('ftp://ftp.ebi.ac.uk/?proxy=test.rebex.net')

    """

    _meta = {
        "invalid_path_chars": "\0",
        "network": True,
        "read_only": False,
        "thread_safe": True,
        "unicode_paths": True,
        "virtual": False,
    }

    def __init__(
        self,
        host,  # type: Text
        user="anonymous",  # type: Text
        passwd="",  # type: Text
        acct="",  # type: Text
        timeout=10,  # type: int
        port=21,  # type: int
        proxy=None,  # type: Optional[Text]
        tls=False,  # type: bool
    ):
        # type: (...) -> None
        """Create a new `FTPFS` instance.

        Arguments:
            host (str): A FTP host, e.g. ``'ftp.mirror.nl'``.
            user (str): A username (default is ``'anonymous'``).
            passwd (str): Password for the server, or `None` for anon.
            acct (str): FTP account.
            timeout (int): Timeout for contacting server (in seconds,
                defaults to 10).
            port (int): FTP port number (default 21).
            proxy (str, optional): An FTP proxy, or ``None`` (default)
                for no proxy.
            tls (bool): Attempt to use FTP over TLS (FTPS) (default: False)

        """
        super(FTPFS, self).__init__()
        self._host = host
        self._user = user
        self.passwd = passwd
        self.acct = acct
        self.timeout = timeout
        self.port = port
        self.proxy = proxy
        self.tls = tls

        if self.tls and isinstance(FTP_TLS, Exception):
            raise_from(errors.CreateFailed("FTP over TLS not supported"), FTP_TLS)

        self.encoding = "latin-1"
        self._ftp = None  # type: Optional[FTP]
        self._welcome = None  # type: Optional[Text]
        self._features = {}  # type: Dict[Text, Text]

    def __repr__(self):
        # type: (...) -> Text
        return "FTPFS({!r}, port={!r})".format(self.host, self.port)

    def __str__(self):
        # type: (...) -> Text
        _fmt = "<ftpfs '{host}'>" if self.port == 21 else "<ftpfs '{host}:{port}'>"
        return _fmt.format(host=self.host, port=self.port)

    @property
    def user(self):
        # type: () -> Text
        return (
            self._user if self.proxy is None else "{}@{}".format(self._user, self._host)
        )

    @property
    def host(self):
        # type: () -> Text
        return self._host if self.proxy is None else self.proxy

    @classmethod
    def _parse_features(cls, feat_response):
        # type: (Text) -> Dict[Text, Text]
        """Parse a dict of features from FTP feat response."""
        features = {}
        if feat_response.split("-")[0] == "211":
            for line in feat_response.splitlines():
                if line.startswith(" "):
                    key, _, value = line[1:].partition(" ")
                    features[key] = value
        return features

    def _open_ftp(self):
        # type: () -> FTP
        """Open a new ftp object."""
        _ftp = FTP_TLS() if self.tls else FTP()
        _ftp.set_debuglevel(0)
        with ftp_errors(self):
            _ftp.connect(self.host, self.port, self.timeout)
            _ftp.login(self.user, self.passwd, self.acct)
            try:
                _ftp.prot_p()  # type: ignore
            except AttributeError:
                pass
            self._features = {}
            try:
                feat_response = _decode(_ftp.sendcmd("FEAT"), "latin-1")
            except error_perm:  # pragma: no cover
                self.encoding = "latin-1"
            else:
                self._features = self._parse_features(feat_response)
                self.encoding = "utf-8" if "UTF8" in self._features else "latin-1"
                if not PY2:
                    _ftp.file = _ftp.sock.makefile(  # type: ignore
                        "r", encoding=self.encoding
                    )
        _ftp.encoding = self.encoding
        self._welcome = _ftp.welcome
        return _ftp

    def _manage_ftp(self):
        # type: () -> ContextManager[FTP]
        ftp = self._open_ftp()
        return manage_ftp(ftp)

    @property
    def ftp_url(self):
        # type: () -> Text
        """Get the FTP url this filesystem will open."""
        if self.port == 21:
            _host_part = self.host
        else:
            _host_part = "{}:{}".format(self.host, self.port)

        if self.user == "anonymous" or self.user is None:
            _user_part = ""
        else:
            _user_part = "{}:{}@".format(self.user, self.passwd)

        scheme = "ftps" if self.tls else "ftp"
        url = "{}://{}{}".format(scheme, _user_part, _host_part)
        return url

    @property
    def ftp(self):
        # type: () -> FTP
        """~ftplib.FTP: the underlying FTP client."""
        return self._get_ftp()

    def geturl(self, path, purpose="download"):
        # type: (str, str) -> Text
        """Get FTP url for resource."""
        _path = self.validatepath(path)
        if purpose != "download":
            raise errors.NoURL(_path, purpose)
        return "{}{}".format(self.ftp_url, _path)

    def _get_ftp(self):
        # type: () -> FTP
        if self._ftp is None:
            self._ftp = self._open_ftp()
        return self._ftp

    @property
    def features(self):  # noqa: D401
        # type: () -> Dict[Text, Text]
        """`dict`: Features of the remote FTP server."""
        self._get_ftp()
        return self._features

    def _read_dir(self, path):
        # type: (Text) -> Dict[Text, Info]
        _path = abspath(normpath(path))
        lines = []  # type: List[Union[ByteString, Text]]
        with ftp_errors(self, path=path):
            self.ftp.retrlines(
                str("LIST ") + _encode(_path, self.ftp.encoding), lines.append
            )
        lines = [
            line.decode("utf-8") if isinstance(line, bytes) else line for line in lines
        ]
        _list = [Info(raw_info) for raw_info in ftp_parse.parse(lines)]
        dir_listing = OrderedDict({info.name: info for info in _list})
        return dir_listing

    @property
    def supports_mlst(self):
        # type: () -> bool
        """bool: whether the server supports MLST feature."""
        return "MLST" in self.features

    @property
    def supports_mdtm(self):
        # type: () -> bool
        """bool: whether the server supports the MDTM feature."""
        return "MDTM" in self.features

    def create(self, path, wipe=False):
        # type: (Text, bool) -> bool
        _path = self.validatepath(path)
        with ftp_errors(self, path):
            if wipe or not self.isfile(path):
                empty_file = io.BytesIO()
                self.ftp.storbinary(
                    str("STOR ") + _encode(_path, self.ftp.encoding), empty_file
                )
                return True
        return False

    @classmethod
    def _parse_ftp_time(cls, time_text):
        # type: (Text) -> Optional[int]
        """Parse a time from an ftp directory listing."""
        try:
            tm_year = int(time_text[0:4])
            tm_month = int(time_text[4:6])
            tm_day = int(time_text[6:8])
            tm_hour = int(time_text[8:10])
            tm_min = int(time_text[10:12])
            tm_sec = int(time_text[12:14])
        except ValueError:
            return None
        epoch_time = calendar.timegm(
            (tm_year, tm_month, tm_day, tm_hour, tm_min, tm_sec)
        )
        return epoch_time

    @classmethod
    def _parse_facts(cls, line):
        # type: (Text) -> Tuple[Optional[Text], Dict[Text, Text]]
        name = None
        facts = {}
        for fact in line.split(";"):
            key, sep, value = fact.partition("=")
            if sep:
                key = key.strip().lower()
                value = value.strip()
                facts[key] = value
            else:
                name = basename(fact.rstrip("/").strip())
        return name if name not in (".", "..") else None, facts

    @classmethod
    def _parse_mlsx(cls, lines):
        # type: (Iterable[Text]) -> Iterator[RawInfo]
        for line in lines:
            name, facts = cls._parse_facts(line.strip())
            if name is None:
                continue
            _type = facts.get("type", "file")
            if _type not in {"dir", "file"}:
                continue
            is_dir = _type == "dir"
            raw_info = {}  # type: Dict[Text, Dict[Text, object]]

            raw_info["basic"] = {"name": name, "is_dir": is_dir}
            raw_info["ftp"] = facts  # type: ignore
            raw_info["details"] = {
                "type": (int(ResourceType.directory if is_dir else ResourceType.file))
            }

            details = raw_info["details"]
            size_str = facts.get("size", facts.get("sizd", "0"))
            size = 0
            if size_str.isdigit():
                size = int(size_str)
            details["size"] = size
            if "modify" in facts:
                details["modified"] = cls._parse_ftp_time(facts["modify"])
            if "create" in facts:
                details["created"] = cls._parse_ftp_time(facts["create"])
            yield raw_info

    if typing.TYPE_CHECKING:

        def opendir(self, path, factory=None):
            # type: (_F, Text, Optional[_OpendirFactory]) -> SubFS[_F]
            pass

    def getinfo(self, path, namespaces=None):
        # type: (Text, Optional[Container[Text]]) -> Info
        _path = self.validatepath(path)
        namespaces = namespaces or ()

        if _path == "/":
            return Info(
                {
                    "basic": {"name": "", "is_dir": True},
                    "details": {"type": int(ResourceType.directory)},
                }
            )

        if self.supports_mlst:
            with self._lock:
                with ftp_errors(self, path=path):
                    response = self.ftp.sendcmd(
                        str("MLST ") + _encode(_path, self.ftp.encoding)
                    )
                lines = _decode(response, self.ftp.encoding).splitlines()[1:-1]
                for raw_info in self._parse_mlsx(lines):
                    return Info(raw_info)

        with ftp_errors(self, path=path):
            dir_name, file_name = split(_path)
            directory = self._read_dir(dir_name)
            if file_name not in directory:
                raise errors.ResourceNotFound(path)
            info = directory[file_name]
            return info

    def getmeta(self, namespace="standard"):
        # type: (Text) -> Dict[Text, object]
        _meta = {}  # type: Dict[Text, object]
        self._get_ftp()
        if namespace == "standard":
            _meta = self._meta.copy()
            _meta["unicode_paths"] = "UTF8" in self.features
            _meta["supports_mtime"] = "MDTM" in self.features
        return _meta

    def getmodified(self, path):
        # type: (Text) -> Optional[datetime.datetime]
        if self.supports_mdtm:
            _path = self.validatepath(path)
            with self._lock:
                with ftp_errors(self, path=path):
                    cmd = "MDTM " + _encode(_path, self.ftp.encoding)
                    response = self.ftp.sendcmd(cmd)
                    mtime = self._parse_ftp_time(response.split()[1])
                    return epoch_to_datetime(mtime)
        return super(FTPFS, self).getmodified(path)

    def listdir(self, path):
        # type: (Text) -> List[Text]
        _path = self.validatepath(path)
        with self._lock:
            dir_list = [info.name for info in self.scandir(_path)]
        return dir_list

    def makedir(
        self,  # type: _F
        path,  # type: Text
        permissions=None,  # type: Optional[Permissions]
        recreate=False,  # type: bool
    ):
        # type: (...) -> SubFS[_F]
        _path = self.validatepath(path)

        with ftp_errors(self, path=path):
            if _path == "/":
                if recreate:
                    return self.opendir(path)
                else:
                    raise errors.DirectoryExists(path)

            if not (recreate and self.isdir(path)):
                try:
                    self.ftp.mkd(_encode(_path, self.ftp.encoding))
                except error_perm as error:
                    code, _ = _parse_ftp_error(error)
                    if code == "550":
                        if self.isdir(path):
                            raise errors.DirectoryExists(path)
                        else:
                            if self.exists(path):
                                raise errors.DirectoryExists(path)
                    raise errors.ResourceNotFound(path)
        return self.opendir(path)

    def openbin(self, path, mode="r", buffering=-1, **options):
        # type: (Text, Text, int, **Any) -> BinaryIO
        _mode = Mode(mode)
        _mode.validate_bin()
        _path = self.validatepath(path)

        with self._lock:
            try:
                info = self.getinfo(_path)
            except errors.ResourceNotFound:
                if _mode.reading:
                    raise errors.ResourceNotFound(path)
                if _mode.writing and not self.isdir(dirname(_path)):
                    raise errors.ResourceNotFound(path)
            else:
                if info.is_dir:
                    raise errors.FileExpected(path)
                if _mode.exclusive:
                    raise errors.FileExists(path)
            ftp_file = FTPFile(self, _path, _mode.to_platform_bin())
        return ftp_file  # type: ignore

    def remove(self, path):
        # type: (Text) -> None
        self.check()
        _path = self.validatepath(path)
        with self._lock:
            if self.isdir(path):
                raise errors.FileExpected(path=path)
            with ftp_errors(self, path):
                self.ftp.delete(_encode(_path, self.ftp.encoding))

    def removedir(self, path):
        # type: (Text) -> None
        _path = self.validatepath(path)
        if _path == "/":
            raise errors.RemoveRootError()

        with ftp_errors(self, path):
            try:
                self.ftp.rmd(_encode(_path, self.ftp.encoding))
            except error_perm as error:
                code, _ = _parse_ftp_error(error)
                if code == "550":
                    if self.isfile(path):
                        raise errors.DirectoryExpected(path)
                    if not self.isempty(path):
                        raise errors.DirectoryNotEmpty(path)
                raise  # pragma: no cover

    def _scandir(self, path, namespaces=None):
        # type: (Text, Optional[Container[Text]]) -> Iterator[Info]
        _path = self.validatepath(path)
        with self._lock:
            if self.supports_mlst:
                lines = []
                with ftp_errors(self, path=path):
                    try:
                        self.ftp.retrlines(
                            str("MLSD ") + _encode(_path, self.ftp.encoding),
                            lambda l: lines.append(_decode(l, self.ftp.encoding)),
                        )
                    except error_perm:
                        if not self.getinfo(path).is_dir:
                            raise errors.DirectoryExpected(path)
                        raise  # pragma: no cover
                if lines:
                    for raw_info in self._parse_mlsx(lines):
                        yield Info(raw_info)
                    return
            for info in self._read_dir(_path).values():
                yield info

    def scandir(
        self,
        path,  # type: Text
        namespaces=None,  # type: Optional[Container[Text]]
        page=None,  # type: Optional[Tuple[int, int]]
    ):
        # type: (...) -> Iterator[Info]
        if not self.supports_mlst and not self.getinfo(path).is_dir:
            raise errors.DirectoryExpected(path)
        iter_info = self._scandir(path, namespaces=namespaces)
        if page is not None:
            start, end = page
            iter_info = itertools.islice(iter_info, start, end)
        return iter_info

    def upload(self, path, file, chunk_size=None, **options):
        # type: (Text, BinaryIO, Optional[int], **Any) -> None
        _path = self.validatepath(path)
        with self._lock:
            with ftp_errors(self, path):
                self.ftp.storbinary(
                    str("STOR ") + _encode(_path, self.ftp.encoding), file
                )

    def writebytes(self, path, contents):
        # type: (Text, ByteString) -> None
        if not isinstance(contents, bytes):
            raise TypeError("contents must be bytes")
        self.upload(path, io.BytesIO(contents))

    def setinfo(self, path, info):
        # type: (Text, RawInfo) -> None
        use_mfmt = False
        if "MFMT" in self.features:
            info_details = None
            if "modified" in info:
                info_details = info["modified"]
            elif "details" in info:
                info_details = info["details"]
            if info_details and "modified" in info_details:
                use_mfmt = True
                mtime = cast(float, info_details["modified"])

        if use_mfmt:
            with ftp_errors(self, path):
                cmd = (
                    "MFMT "
                    + datetime.datetime.utcfromtimestamp(mtime).strftime("%Y%m%d%H%M%S")
                    + " "
                    + _encode(path, self.ftp.encoding)
                )
                try:
                    self.ftp.sendcmd(cmd)
                except error_perm:
                    pass
        else:
            if not self.exists(path):
                raise errors.ResourceNotFound(path)

    def readbytes(self, path):
        # type: (Text) -> bytes
        _path = self.validatepath(path)
        data = io.BytesIO()
        with ftp_errors(self, path):
            with self._manage_ftp() as ftp:
                try:
                    ftp.retrbinary(
                        str("RETR ") + _encode(_path, self.ftp.encoding), data.write
                    )
                except error_perm as error:
                    code, _ = _parse_ftp_error(error)
                    if code == "550":
                        if self.isdir(path):
                            raise errors.FileExpected(path)
                    raise

        data_bytes = data.getvalue()
        return data_bytes

    def close(self):
        # type: () -> None
        if not self.isclosed():
            try:
                self.ftp.quit()
            except Exception:  # pragma: no cover
                pass
            self._ftp = None
        super(FTPFS, self).close()
