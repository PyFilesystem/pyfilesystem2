"""Manage the filesystem in a Tar archive.
"""

from __future__ import print_function
from __future__ import unicode_literals

import operator
import os
import tarfile
import typing
from collections import OrderedDict
from typing import cast, IO

import six
from six.moves import map

from . import errors
from .base import FS
from .compress import write_tar
from .enums import ResourceType
from .errors import IllegalBackReference, NoURL
from .info import Info
from .iotools import RawWrapper
from .opener import open_fs
from .permissions import Permissions
from ._url_tools import url_quote
from .path import (
    dirname,
    join,
    relpath,
    basename,
    isbase,
    normpath,
    parts,
    frombase,
    recursepath,
    relativefrom,
)
from .wrapfs import WrapFS

if typing.TYPE_CHECKING:
    from tarfile import TarInfo
    from typing import (
        Any,
        BinaryIO,
        Collection,
        Dict,
        List,
        Optional,
        Text,
        Tuple,
        Union,
    )
    from .info import RawInfo
    from .subfs import SubFS

    T = typing.TypeVar("T", bound="ReadTarFS")


__all__ = ["TarFS", "WriteTarFS", "ReadTarFS"]


if six.PY2:

    def _get_member_info(member, encoding):
        # type: (TarInfo, Text) -> Dict[Text, object]
        return member.get_info(encoding, None)


else:

    def _get_member_info(member, encoding):
        # type: (TarInfo, Text) -> Dict[Text, object]
        # NOTE(@althonos): TarInfo.get_info is neither in the doc nor
        #     in the `tarfile` stub, and yet it exists and is public !
        return member.get_info()  # type: ignore


class TarFS(WrapFS):
    """Read and write tar files.

    There are two ways to open a TarFS for the use cases of reading
    a tar file, and creating a new one.

    If you open the TarFS with  ``write`` set to `False` (the
    default), then the filesystem will be a read only filesystem which
    maps to the files and directories within the tar file. Files are
    decompressed on the fly when you open them.

    Here's how you might extract and print a readme from a tar file::

        with TarFS('foo.tar.gz') as tar_fs:
            readme = tar_fs.readtext('readme.txt')

    If you open the TarFS with ``write`` set to `True`, then the TarFS
    will be a empty temporary filesystem. Any files / directories you
    create in the TarFS will be written in to a tar file when the TarFS
    is closed. The compression is set from the new file name but may be
    set manually with the ``compression`` argument.

    Here's how you might write a new tar file containing a readme.txt
    file::

        with TarFS('foo.tar.xz', write=True) as new_tar:
            new_tar.writetext(
                'readme.txt',
                'This tar file was written by PyFilesystem'
            )

    Arguments:
        file (str or io.IOBase): An OS filename, or an open file handle.
        write (bool): Set to `True` to write a new tar file, or
            use default (`False`) to read an existing tar file.
        compression (str, optional): Compression to use (one of the formats
            supported by `tarfile`: ``xz``, ``gz``, ``bz2``, or `None`).
        temp_fs (str): An FS URL for the temporary filesystem
            used to store data prior to tarring.

    """

    _compression_formats = {
        # FMT    #UNIX      #MSDOS
        "xz": (".tar.xz", ".txz"),
        "bz2": (".tar.bz2", ".tbz"),
        "gz": (".tar.gz", ".tgz"),
    }

    def __new__(  # type: ignore
        cls,
        file,  # type: Union[Text, BinaryIO]
        write=False,  # type: bool
        compression=None,  # type: Optional[Text]
        encoding="utf-8",  # type: Text
        temp_fs="temp://__tartemp__",  # type: Text
    ):
        # type: (...) -> FS
        if isinstance(file, (six.text_type, six.binary_type)):
            file = os.path.expanduser(file)
            filename = file  # type: Text
        else:
            filename = getattr(file, "name", "")

        if write and compression is None:
            compression = None
            for comp, extensions in six.iteritems(cls._compression_formats):
                if filename.endswith(extensions):
                    compression = comp
                    break

        if write:
            return WriteTarFS(
                file, compression=compression, encoding=encoding, temp_fs=temp_fs
            )
        else:
            return ReadTarFS(file, encoding=encoding)

    if typing.TYPE_CHECKING:

        def __init__(
            self,
            file,  # type: Union[Text, BinaryIO]
            write=False,  # type: bool
            compression=None,  # type: Optional[Text]
            encoding="utf-8",  # type: Text
            temp_fs="temp://__tartemp__",  # type: Text
        ):
            # type: (...) -> None
            pass


@six.python_2_unicode_compatible
class WriteTarFS(WrapFS):
    """A writable tar file."""

    def __init__(
        self,
        file,  # type: Union[Text, BinaryIO]
        compression=None,  # type: Optional[Text]
        encoding="utf-8",  # type: Text
        temp_fs="temp://__tartemp__",  # type: Text
    ):
        # type: (...) -> None
        self._file = file  # type: Union[Text, BinaryIO]
        self.compression = compression
        self.encoding = encoding
        self._temp_fs_url = temp_fs
        self._temp_fs = open_fs(temp_fs)
        self._meta = dict(self._temp_fs.getmeta())  # type: ignore
        super(WriteTarFS, self).__init__(self._temp_fs)

    def __repr__(self):
        # type: () -> Text
        t = "WriteTarFS({!r}, compression={!r}, encoding={!r}, temp_fs={!r})"
        return t.format(self._file, self.compression, self.encoding, self._temp_fs_url)

    def __str__(self):
        # type: () -> Text
        return "<TarFS-write '{}'>".format(self._file)

    def delegate_path(self, path):
        # type: (Text) -> Tuple[FS, Text]
        return self._temp_fs, path

    def delegate_fs(self):
        # type: () -> FS
        return self._temp_fs

    def close(self):
        # type: () -> None
        if not self.isclosed():
            try:
                self.write_tar()
            finally:
                self._temp_fs.close()
        super(WriteTarFS, self).close()

    def write_tar(
        self,
        file=None,  # type: Union[Text, BinaryIO, None]
        compression=None,  # type: Optional[Text]
        encoding=None,  # type: Optional[Text]
    ):
        # type: (...) -> None
        """Write tar to a file.

        Arguments:
            file (str or io.IOBase, optional): Destination file, may be
                a file name or an open file object.
            compression (str, optional): Compression to use (one of
                the constants defined in `tarfile` in the stdlib).
            encoding (str, optional): The character encoding to use
                (default uses the encoding defined in
                `~WriteTarFS.__init__`).

        Note:
            This is called automatically when the TarFS is closed.
        """
        if not self.isclosed():
            write_tar(
                self._temp_fs,
                file or self._file,
                compression=compression or self.compression,
                encoding=encoding or self.encoding,
            )


@six.python_2_unicode_compatible
class ReadTarFS(FS):
    """A readable tar file."""

    _meta = {
        "case_insensitive": True,
        "network": False,
        "read_only": True,
        "supports_rename": False,
        "thread_safe": True,
        "unicode_paths": True,
        "virtual": False,
    }

    _typemap = type_map = {
        tarfile.BLKTYPE: ResourceType.block_special_file,
        tarfile.CHRTYPE: ResourceType.character,
        tarfile.DIRTYPE: ResourceType.directory,
        tarfile.FIFOTYPE: ResourceType.fifo,
        tarfile.REGTYPE: ResourceType.file,
        tarfile.AREGTYPE: ResourceType.file,
        tarfile.SYMTYPE: ResourceType.symlink,
        tarfile.CONTTYPE: ResourceType.file,
        tarfile.LNKTYPE: ResourceType.symlink,
        # this is how we mark implicit directories
        tarfile.DIRTYPE + b"i": ResourceType.directory,
    }

    @errors.CreateFailed.catch_all
    def __init__(self, file, encoding="utf-8"):
        # type: (Union[Text, BinaryIO], Text) -> None
        super(ReadTarFS, self).__init__()
        self._file = file
        self.encoding = encoding
        if isinstance(file, (six.text_type, six.binary_type)):
            self._tar = tarfile.open(file, mode="r")
        else:
            self._tar = tarfile.open(fileobj=file, mode="r")

        self._directory_cache = None

    @property
    def _directory_entries(self):
        """Lazy directory cache."""
        if self._directory_cache is None:
            _decode = self._decode
            _encode = self._encode

            # collect all directory entries and remove slashes
            _directory_entries = (
                (_decode(info.name).strip("/"), info) for info in self._tar
            )

            # build the cache first before updating it to reduce chances
            # of data races
            _cache = OrderedDict()
            for name, info in _directory_entries:
                # check for any invalid back references
                try:
                    _name = normpath(name)
                except IllegalBackReference:
                    continue

                # add all implicit dirnames if not in the cache already
                for partial_name in map(relpath, recursepath(_name)):
                    dirinfo = tarfile.TarInfo(self._encode(partial_name))
                    dirinfo.type = tarfile.DIRTYPE
                    _cache.setdefault(partial_name, dirinfo)

                # add the entry itself, potentially overwriting implicit entries
                _cache[_name] = info

            self._directory_cache = _cache
        return self._directory_cache

    def _follow_symlink(self, entry):
        """Follow an symlink `TarInfo` to find a concrete entry."""
        _entry = entry
        while _entry.issym():
            linkname = normpath(
                join(dirname(self._decode(_entry.name)), self._decode(_entry.linkname))
            )
            resolved = self._resolve(linkname)
            if resolved is None:
                raise errors.ResourceNotFound(linkname)
            _entry = self._directory_entries[resolved]

        return _entry

    def _resolve(self, path):
        """Replace path components that are symlinks with concrete components.

        Returns:


        """
        if path in self._directory_entries or not path:
            return path
        for prefix in map(relpath, reversed(recursepath(path))):
            suffix = relativefrom(prefix, path)
            entry = self._directory_entries.get(prefix)
            if entry is not None and entry.issym():
                entry = self._follow_symlink(entry)
                return self._resolve(join(self._decode(entry.name), suffix))
        return None

    def __repr__(self):
        # type: () -> Text
        return "ReadTarFS({!r})".format(self._file)

    def __str__(self):
        # type: () -> Text
        return "<TarFS '{}'>".format(self._file)

    if six.PY2:

        def _encode(self, s):
            # type: (Text) -> str
            return s.encode(self.encoding)

        def _decode(self, s):
            # type: (str) -> Text
            return s.decode(self.encoding)

    else:

        def _encode(self, s):
            # type: (Text) -> str
            return s

        def _decode(self, s):
            # type: (str) -> Text
            return s

    def getinfo(self, path, namespaces=None):
        # type: (Text, Optional[Collection[Text]]) -> Info
        _path = relpath(self.validatepath(path))
        namespaces = namespaces or ()
        raw_info = {}  # type: Dict[Text, Dict[Text, object]]

        # special case for root
        if not _path:
            raw_info["basic"] = {"name": "", "is_dir": True}
            if "details" in namespaces:
                raw_info["details"] = {"type": int(ResourceType.directory)}

        else:

            _realpath = self._resolve(_path)
            if _realpath is None:
                raise errors.ResourceNotFound(path)

            implicit = False
            member = self._directory_entries[_realpath]

            raw_info["basic"] = {
                "name": basename(self._decode(member.name)),
                "is_dir": self.isdir(_path),  # is_dir should follow symlinks
            }

            if "link" in namespaces:
                if member.issym():
                    target = join(
                        dirname(self._decode(member.name)),
                        self._decode(member.linkname),
                    )
                else:
                    target = None
                raw_info["link"] = {"target": target}
            if "details" in namespaces:
                raw_info["details"] = {
                    "size": member.size,
                    "type": int(self.type_map[member.type]),
                }
                if not implicit:
                    raw_info["details"]["modified"] = member.mtime
            if "access" in namespaces and not implicit:
                raw_info["access"] = {
                    "gid": member.gid,
                    "group": member.gname,
                    "permissions": Permissions(mode=member.mode).dump(),
                    "uid": member.uid,
                    "user": member.uname,
                }
            if "tar" in namespaces and not implicit:
                raw_info["tar"] = _get_member_info(member, self.encoding)
                raw_info["tar"].update(
                    {
                        k.replace("is", "is_"): getattr(member, k)()
                        for k in dir(member)
                        if k.startswith("is")
                    }
                )

        return Info(raw_info)

    def isdir(self, path):
        _path = relpath(self.validatepath(path))
        realpath = self._resolve(_path)
        if realpath is not None:
            entry = self._directory_entries[realpath]
            return self._follow_symlink(entry).isdir()
        else:
            return False

    def isfile(self, path):
        _path = relpath(self.validatepath(path))
        realpath = self._resolve(_path)
        if realpath is not None:
            entry = self._directory_entries[realpath]
            return self._follow_symlink(entry).isfile()
        else:
            return False

    def islink(self, path):
        _path = relpath(self.validatepath(path))
        realpath = self._resolve(_path)
        if realpath is not None:
            entry = self._directory_entries[realpath]
            return entry.issym()
        else:
            return False

    def setinfo(self, path, info):
        # type: (Text, RawInfo) -> None
        self.check()
        raise errors.ResourceReadOnly(path)

    def listdir(self, path):
        # type: (Text) -> List[Text]
        _path = relpath(self.validatepath(path))

        # check the given path exists
        realpath = self._resolve(_path)
        if realpath is None:
            raise errors.ResourceNotFound(path)
        elif realpath:
            target = self._follow_symlink(self._directory_entries[realpath])
            # check the path is either a symlink mapping to a directory or a directory
            if target.isdir():
                base = target.name
            elif target.issym():
                base = target.linkname
            else:
                raise errors.DirectoryExpected(path)
        else:
            base = ""

        # find all entries in the actual directory
        children = (
            frombase(base, n) for n in self._directory_entries if isbase(base, n)
        )
        content = (parts(child)[1] for child in children if relpath(child))

        return list(OrderedDict.fromkeys(content))

    def makedir(
        self,  # type: T
        path,  # type: Text
        permissions=None,  # type: Optional[Permissions]
        recreate=False,  # type: bool
    ):
        # type: (...) -> SubFS[T]
        self.check()
        raise errors.ResourceReadOnly(path)

    def openbin(self, path, mode="r", buffering=-1, **options):
        # type: (Text, Text, int, **Any) -> BinaryIO
        _path = relpath(self.validatepath(path))

        # check the requested mode is only a reading mode
        if "w" in mode or "+" in mode or "a" in mode:
            raise errors.ResourceReadOnly(path)

        # check the path actually resolves after following symlinks
        _realpath = self._resolve(_path)
        if _realpath is None:
            raise errors.ResourceNotFound(path)

        # TarFile.extractfile returns None if the entry is not a file
        # neither a file nor a symlink
        reader = self._tar.extractfile(self._directory_entries[_realpath])
        if reader is None:
            raise errors.FileExpected(path)

        rw = RawWrapper(reader)
        if six.PY2:  # Patch nonexistent file.flush in Python2

            def _flush():
                pass

            rw.flush = _flush

        return rw  # type: ignore

    def remove(self, path):
        # type: (Text) -> None
        self.check()
        raise errors.ResourceReadOnly(path)

    def removedir(self, path):
        # type: (Text) -> None
        self.check()
        raise errors.ResourceReadOnly(path)

    def close(self):
        # type: () -> None
        super(ReadTarFS, self).close()
        if hasattr(self, "_tar"):
            self._tar.close()

    def isclosed(self):
        # type: () -> bool
        return self._tar.closed  # type: ignore

    def geturl(self, path, purpose="download"):
        # type: (Text, Text) -> Text
        if purpose == "fs" and isinstance(self._file, six.string_types):
            quoted_file = url_quote(self._file)
            quoted_path = url_quote(path)
            return "tar://{}!/{}".format(quoted_file, quoted_path)
        else:
            raise NoURL(path, purpose)


if __name__ == "__main__":  # pragma: no cover
    from fs.tree import render

    with TarFS("tests.tar") as tar_fs:
        print(tar_fs.listdir("/"))
        print(tar_fs.listdir("/tests/"))
        print(tar_fs.readtext("tests/ttt/settings.ini"))
        render(tar_fs)
        print(tar_fs)
        print(repr(tar_fs))

    with TarFS("TarFS.tar", write=True) as tar_fs:
        tar_fs.makedirs("foo/bar")
        tar_fs.writetext("foo/bar/baz.txt", "Hello, World")
        print(tar_fs)
        print(repr(tar_fs))
