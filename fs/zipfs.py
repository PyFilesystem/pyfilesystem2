from __future__ import print_function
from __future__ import unicode_literals

from datetime import datetime
import zipfile

import six

from . import errors
from .base import FS
from .compress import write_zip
from .enums import ResourceType
from .info import Info
from .iotools import RawWrapper
from .memoryfs import MemoryFS
from .opener import open_fs
from .path import dirname, normpath, relpath
from .time import datetime_to_epoch
from .wrapfs import WrapFS


class ZipFS(WrapFS):
    """
    Read and write zip files.

    There are two ways to open a ZipFS for the use cases of reading
    a zip file, and creating a new one.

    If you open the ZipFS with  ``write`` set to ``False`` (the
    default), then the filesystem will be a read only filesystem which
    maps to the files and directories within the zip file. Files are
    decompressed on the fly when you open them.

    Here's how you might extract and print a readme from a zip file::

        with ZipFS('foo.zip') as zip_fs:
            readme = zip_fs.gettext('readme.txt')

    If you open the ZipFS with ``write`` set to ``True``, then the ZipFS
    will be a empty temporary filesystem. Any files / directories you
    create in the ZipFS will be written in to a zip file when the ZipFS
    is closed.

    Here's how you might write a new zip file containing a readme.txt
    file::

        with ZipFS('foo.zip', write=True) as new_zip:
            new_zip.settext(
                'readme.txt',
                'This zip file was written by PyFilesystem'
            )


    :param file: An OS filename, or a open file object.
    :type file: str or file
    :param write: Set to ``True`` to write a new zip file, or ``False``
        to read an existing zip file.
    :type write: bool
    :param compression:  Compression to use (one of the constants
        defined in the zipfile module in the stdlib).
    :type compression: int
    :param temp_fs: An opener string for the temporary filesystem
        used to store data prior to zipping.
    :type temp_fs: str

    """

    def __new__(cls,
                file,
                write=False,
                compression=zipfile.ZIP_DEFLATED,
                encoding="utf-8",
                temp_fs="temp://__ziptemp__"):
        # This magic returns a different class instance based on the
        # value of the ``write`` parameter.
        if write:
            return WriteZipFS(file,
                              compression=compression,
                              encoding=encoding,
                              temp_fs=temp_fs)
        else:
            return ReadZipFS(file, encoding=encoding)


@six.python_2_unicode_compatible
class WriteZipFS(WrapFS):
    """A writable zip file."""

    def __init__(self,
                 file,
                 compression=zipfile.ZIP_DEFLATED,
                 encoding="utf-8",
                 temp_fs="temp://__ziptemp__"):
        self._file = file
        self.compression = compression
        self.encoding = encoding
        self._temp_fs_url = temp_fs
        self._temp_fs = open_fs(temp_fs)
        self._meta = self._temp_fs.getmeta().copy()
        super(WriteZipFS, self).__init__(self._temp_fs)

    def __repr__(self):
        t = "WriteZipFS({!r}, compression={!r}, encoding={!r}, temp_fs={!r})"
        return t.format(
            self._file,
            self.compression,
            self.encoding,
            self._temp_fs_url
        )

    def __str__(self):
        return "<zipfs-write '{}'>".format(self._file)

    def delegate_path(self, path):
        return self._temp_fs, path

    def delegate_fs(self):
        return self._temp_fs

    def close(self):
        if not self.isclosed():
            try:
                self.write_zip()
            finally:
                self._temp_fs.close()
        super(WriteZipFS, self).close()

    def write_zip(self, file=None, compression=None, encoding=None):
        """
        Write zip to a file.

        .. note ::
            This is called automatically when the ZipFS is closed.

        :param file: Destination file, may be a file name or an open
            file object.
        :type file: str or file-like
        :param compression: Compression to use (one of the constants
            defined in the zipfile module in the stdlib).

        """
        if not self.isclosed():
            write_zip(
                self._temp_fs,
                file or self._file,
                compression=compression or self.compression,
                encoding=encoding or self.encoding
            )


@six.python_2_unicode_compatible
class ReadZipFS(FS):
    """A readable zip file."""

    _meta = {
        'case_insensitive': True,
        'network': False,
        'read_only': True,
        'supports_rename': False,
        'thread_safe': True,
        'unicode_paths': True,
        'virtual': False,
    }

    def __init__(self, file, encoding='utf-8'):
        super(ReadZipFS, self).__init__()
        self._file = file
        self.encoding = encoding
        self._zip = zipfile.ZipFile(file, 'r')
        self._directory_fs = None

    def __repr__(self):
        return "ReadZipFS({!r})".format(self._file)

    def __str__(self):
        return "<zipfs '{}'>".format(self._file)

    def _path_to_zip_name(self, path):
        """Convert a path to a zip file name."""
        if self._directory.isdir(path):
            return relpath(normpath(path)) + '/'
        else:
            return relpath(normpath(path))

    @property
    def _directory(self):
        """
        Make a memory filesystem with the same directory structure
        as the zip.

        """
        self.check()
        with self._lock:
            if self._directory_fs is None:
                self._directory_fs = _fs = MemoryFS()
                for zip_name in self._zip.namelist():
                    resource_name = zip_name
                    if six.PY2:
                        resource_name =\
                            resource_name.decode(self.encoding, 'replace')
                    if resource_name.endswith('/'):
                        _fs.makedirs(resource_name, recreate=True)
                    else:
                        _fs.makedirs(dirname(resource_name), recreate=True)
                        _fs.create(resource_name)
            return self._directory_fs

    def getinfo(self, path, namespaces=None):
        self.check()
        namespaces = namespaces or ()
        _path = normpath(path)
        if _path == '/':
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
            basic_info = self._directory.getinfo(_path)
            zip_name = self._path_to_zip_name(path)
            try:
                zip_info = self._zip.getinfo(zip_name)
            except KeyError:
                # Can occur if there is an implied directory in the zip
                raw_info = {
                    "basic":
                    {
                        "name": basic_info.name,
                        "is_dir": basic_info.is_dir
                    }
                }
            else:
                modified_epoch = datetime_to_epoch(
                    datetime(*zip_info.date_time)
                )
                raw_zip_info = {
                    k: getattr(zip_info, k)
                    for k in dir(zip_info)
                    if (not k.startswith('_') and
                        not callable(getattr(zip_info, k)))
                }
                raw_info = {
                    "basic":
                    {
                        "name": basic_info.name,
                        "is_dir": basic_info.is_dir,
                    },
                    "details":
                    {
                        "size": zip_info.file_size,
                        "type": int(
                            ResourceType.directory
                            if basic_info.is_dir else
                            ResourceType.file
                        ),
                        "modified": modified_epoch
                    },
                    "zip": raw_zip_info
                }

        return Info(raw_info)

    def setinfo(self, path, info):
        self.check()
        raise errors.ResourceReadOnly(path)

    def listdir(self, path):
        self.check()
        return self._directory.listdir(path)

    def makedir(self, path, permissions=None, recreate=False):
        self.check()
        raise errors.ResourceReadOnly(path)

    def openbin(self, path, mode="r", buffering=-1, **kwargs):
        self.check()
        if 'w' in mode or '+' in mode or 'a' in mode:
            raise errors.ResourceReadOnly(path)

        if not self._directory.exists(path):
            raise errors.ResourceNotFound(path)
        elif self._directory.isdir(path):
            raise errors.FileExpected(path)

        zip_name = self._path_to_zip_name(path)
        bin_file = self._zip.open(zip_name, 'r')
        return RawWrapper(bin_file)

    def remove(self, path):
        self.check()
        raise errors.ResourceReadOnly(path)

    def removedir(self, path):
        self.check()
        raise errors.ResourceReadOnly(path)

    def close(self):
        super(ReadZipFS, self).close()
        self._zip.close()

    def getbytes(self, path):
        self.check()
        if not self._directory.isfile(path):
            raise errors.ResourceNotFound(path)
        zip_name = self._path_to_zip_name(path)
        zip_bytes = self._zip.read(zip_name)
        return zip_bytes


if __name__ == "__main__":  # pragma: nocover
    from fs.tree import render
    from fs.opener import open_fs

    with ZipFS('tests.zip') as zip_fs:
        print(zip_fs.listdir('/'))
        print(zip_fs.listdir('/tests/'))
        print(zip_fs.gettext('tests/ttt/settings.ini'))
        render(zip_fs)
        print(zip_fs)
        print(repr(zip_fs))

    with ZipFS("zipfs.zip", write=True) as zip_fs:
        zip_fs.makedirs('foo/bar')
        zip_fs.settext('foo/bar/baz.txt', 'Hello, World')
        print(zip_fs)
        print(repr(zip_fs))
