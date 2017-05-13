from __future__ import print_function
from __future__ import unicode_literals

import tarfile
import six

from . import errors
from .base import FS
from .compress import write_tar
from .enums import ResourceType
from .info import Info
from .iotools import RawWrapper
from .opener import open_fs
from .path import dirname, normpath, relpath, basename
from .wrapfs import WrapFS
from .permissions import Permissions


class TarFS(WrapFS):
    """
    Read and write tar files.

    There are two ways to open a TarFS for the use cases of reading
    a tar file, and creating a new one.

    If you open the TarFS with  ``write`` set to ``False`` (the
    default), then the filesystem will be a read only filesystem which
    maps to the files and directories within the tar file. Files are
    decompressed on the fly when you open them.

    Here's how you might extract and print a readme from a tar file::

        with TarFS('foo.tar.gz') as tar_fs:
            readme = tar_fs.gettext('readme.txt')

    If you open the TarFS with ``write`` set to ``True``, then the TarFS
    will be a empty temporary filesystem. Any files / directories you
    create in the TarFS will be written in to a tar file when the TarFS
    is closed. The compression is set from the new file name but may be
    set manually with the ``compression`` argument.

    Here's how you might write a new tar file containing a readme.txt
    file::

        with TarFS('foo.tar.xz', write=True) as new_tar:
            new_tar.settext(
                'readme.txt',
                'This tar file was written by PyFilesystem'
            )

    :param file: An OS filename, or a open file object.
    :type file: str or file
    :param write: Set to ``True`` to write a new tar file, or ``False``
        to read an existing tar file.
    :type write: bool
    :param compression:  Compression to use (one of the formats
        supported by ``tarfile``: ``xz``, ``gz``, ``bz2``, or None).
    :type compression: str
    :param temp_fs: An opener string for the temporary filesystem
        used to store data prior to tarring.
    :type temp_fs: str

    """

    _compression_formats = {
        #FMT    #UNIX      #MSDOS
        'xz': ('.tar.xz', '.txz'),
        'bz2': ('.tar.bz2', '.tbz'),
        'gz': ('.tar.gz', '.tgz'),
    }

    def __new__(cls,
                file,
                write=False,
                compression=None,
                encoding="utf-8",
                temp_fs="temp://__tartemp__"):

        filename = str(getattr(file, 'name', file))

        if write and compression is None:
            compression = None
            for comp, extensions in six.iteritems(cls._compression_formats):
                if filename.endswith(extensions):
                    compression = comp
                    break

        if write:
            return WriteTarFS(file,
                              compression=compression,
                              encoding=encoding,
                              temp_fs=temp_fs)
        # else:
        return ReadTarFS(file, encoding=encoding)


@six.python_2_unicode_compatible
class WriteTarFS(WrapFS):
    """A writable tar file."""

    def __init__(self,
                 file,
                 compression=None,
                 encoding="utf-8",
                 temp_fs="temp://__tartemp__"):
        self._file = file
        self.compression = compression
        self.encoding = encoding
        self._temp_fs_url = temp_fs
        self._temp_fs = open_fs(temp_fs)
        self._meta = self._temp_fs.getmeta().copy()
        super(WriteTarFS, self).__init__(self._temp_fs)

    def __repr__(self):
        t = "WriteTarFS({!r}, compression={!r}, encoding={!r}, temp_fs={!r})"
        return t.format(
            self._file,
            self.compression,
            self.encoding,
            self._temp_fs_url
        )

    def __str__(self):
        return "<TarFS-write '{}'>".format(self._file)

    def delegate_path(self, path):
        return self._temp_fs, path

    def delegate_fs(self):
        return self._temp_fs

    def close(self):
        if not self.isclosed():
            try:
                self.write_tar()
            finally:
                self._temp_fs.close()
        super(WriteTarFS, self).close()

    def write_tar(self, file=None, compression=None, encoding=None):
        """
        Write tar to a file.

        .. note::
            This is called automatically when the TarFS is closed.

        :param file: Destination file, may be a file name or an open
            file object.
        :type file: str or file-like
        :param compression: Compression to use (one of the constants
            defined in the tarfile module in the stdlib).

        """
        if not self.isclosed():
            write_tar(
                self._temp_fs,
                file or self._file,
                compression=compression or self.compression,
                encoding=encoding or self.encoding
            )


@six.python_2_unicode_compatible
class ReadTarFS(FS):
    """A readable tar file."""

    _meta = {
        'case_insensitive': True,
        'network': False,
        'read_only': True,
        'supports_rename': False,
        'thread_safe': True,
        'unicode_paths': True,
        'virtual': False,
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
    }

    def __init__(self, file, encoding='utf-8'):
        super(ReadTarFS, self).__init__()
        self._file = file
        self.encoding = encoding
        if hasattr(file, 'read'):
            self._tar = tarfile.open(fileobj=file, mode='r')
        else:
            self._tar = tarfile.open(file, mode='r')

    def __repr__(self):
        return "ReadTarFS({!r})".format(self._file)

    def __str__(self):
        return "<TarFS '{}'>".format(self._file)

    def getinfo(self, path, namespaces=None):
        self.check()
        namespaces = namespaces or ()
        path = relpath(normpath(path))
        if not path:
            raw_info = {
                "basic":
                {
                    "name": "",
                    "is_dir": True,
                },
                "details":
                {
                    "type": int(ResourceType.directory)
                }
            }
        else:
            try:
                member = self._tar.getmember(path)
            except KeyError:
                raise errors.ResourceNotFound(path)


            raw_tar_info = member.get_info(*(
                [self.encoding, None] if six.PY2 else []
            ))

            raw_tar_info.update({
                k.replace('is', 'is_'):getattr(member, k)()
                for k in dir(member)
                if k.startswith('is')
            })
            raw_info = {
                "basic":
                {
                    "name": basename(member.name),
                    "is_dir": member.isdir(),
                },
                "details":
                {
                    "size": member.size,
                    "type": int(self.type_map[member.type]),
                    "modified": member.mtime,
                },
                "access":
                {
                    "gid": member.gid,
                    "group": member.gname,
                    "permissions": Permissions(mode=member.mode).dump(),
                    "uid": member.uid,
                    "user": member.uname,
                },
                "tar": raw_tar_info,
            }
        return Info(raw_info)

    def setinfo(self, path, info):
        self.check()
        raise errors.ResourceReadOnly(path)

    def listdir(self, path):
        self.check()
        path = relpath(path)
        if path:
            try:
                member = self._tar.getmember(path)
            except KeyError:
                six.raise_from(errors.ResourceNotFound(path), None)
            else:
                if not member.isdir():
                    six.raise_from(errors.DirectoryExpected(path), None)

        return [
            basename(member.name)
            for member in self._tar
            if dirname(member.path) == path
        ]

    def makedir(self, path, permissions=None, recreate=False):
        self.check()
        raise errors.ResourceReadOnly(path)

    def openbin(self, path, mode="r", buffering=-1, **options):
        self.check()
        path = relpath(normpath(path))

        if 'w' in mode or '+' in mode or 'a' in mode:
            raise errors.ResourceReadOnly(path)

        try:
            member = self._tar.getmember(path)
        except KeyError:
            six.raise_from(errors.ResourceNotFound(path), None)

        if not member.isfile():
            raise errors.FileExpected(path)

        rw = RawWrapper(self._tar.extractfile(member))

        if six.PY2: # Patch nonexistent file.flush in Python2
            def _flush():
                pass
            rw.flush = _flush

        return rw

    def remove(self, path):
        self.check()
        raise errors.ResourceReadOnly(path)

    def removedir(self, path):
        self.check()
        raise errors.ResourceReadOnly(path)

    def close(self):
        super(ReadTarFS, self).close()
        self._tar.close()

    def isclosed(self):
        return self._tar.closed


if __name__ == "__main__":  # pragma: nocover
    from fs.tree import render
    from fs.opener import open_fs

    with TarFS('tests.tar') as tar_fs:
        print(tar_fs.listdir('/'))
        print(tar_fs.listdir('/tests/'))
        print(tar_fs.gettext('tests/ttt/settings.ini'))
        render(tar_fs)
        print(tar_fs)
        print(repr(tar_fs))

    with TarFS("TarFS.tar", write=True) as tar_fs:
        tar_fs.makedirs('foo/bar')
        tar_fs.settext('foo/bar/baz.txt', 'Hello, World')
        print(tar_fs)
        print(repr(tar_fs))
