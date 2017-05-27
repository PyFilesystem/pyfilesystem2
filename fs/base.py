"""
fs.base
========

PyFilesystem base class


"""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import abc
import os
import threading
import time
from functools import partial

from contextlib import closing
import itertools

import six

from . import copy
from . import errors
from . import iotools
from . import move
from . import tools
from . import walk
from . import wildcard
from .mode import validate_open_mode
from .path import abspath
from .path import join
from .path import normpath
from .time import datetime_to_epoch
from .walk import Walker


@six.add_metaclass(abc.ABCMeta)
class FS(object):
    """Base class for FS objects."""

    # This is the "standard" meta namespace.
    _meta = {}

    def __init__(self):
        self._closed = False
        self._lock = threading.RLock()
        super(FS, self).__init__()

    def __enter__(self):
        """Allow use of filesystem as a context manager."""
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Close filesystem on exit."""
        self.close()

    @property
    def walk(self):
        """
        Get a :class:`~fs.walk.BoundWalker` object for this filesystem.

        """
        return Walker.bind(self)

    # ---------------------------------------------------------------- #
    # Required methods                                                 #
    # Filesystems must implement these methods.                        #
    # ---------------------------------------------------------------- #

    @abc.abstractmethod
    def getinfo(self, path, namespaces=None):
        """
        Get information regarding a resource (file or directory) on a
        filesystem.

        :param str path: A path to a resource on the filesystem.
        :param namespaces: Info namespaces to query (defaults to
            'basic').
        :type namespaces: list or None
        :returns: Resource information object.
        :rtype: :class:`~fs.info.Info`

        For more information regarding resource information see
        :ref:`info`.

        """

    @abc.abstractmethod
    def listdir(self, path):
        """
        Get a list of the resource names in a directory.

        :param str path: A path to a directory on the filesystem.
        :return: list of names, relative to ``path``.
        :rtype: list

        :raises fs.errors.DirectoryExpected: If `path` is not a
            directory.
        :raises fs.errors.ResourceNotFound: If `path` does not exist.

        This method will return a list of the resources in a directory.
        A 'resource' is a file, directory, or one of the other types
        defined in :class:`~fs.ResourceType`.

        """

    @abc.abstractmethod
    def makedir(self, path, permissions=None, recreate=False):
        """
        Make a directory, and return a :class:`~fs.subfs.SubFS` for
        the new directory.

        :param str path: Path to directory from root.
        :param permissions: :class:`~fs.permissions.Permissions`
            instance.
        :type permissions: Permissions
        :param bool recreate: Do not raise an error if the directory exists.
        :rtype: :class:`~fs.subfs.SubFS`

        :raises fs.errors.DirectoryExists: if the path already exists.
        :raises fs.errors.ResourceNotFound: if the path is not found.

        """

    @abc.abstractmethod
    def openbin(self, path, mode="r", buffering=-1, **options):
        """
        Open a binary file-like object.

        :param str path: A path on the filesystem.
        :param str mode: Mode to open file (must be a valid non-text
            mode). Since this method only opens binary files, the `b` in
            the mode string is implied.
        :param buffering: Buffering policy (-1  to use default
            buffering, 0 to disable buffering, or positive integer to
            indicate buffer size).
        :type buffering: int
        :param options: Keyword parameters for any additional
            information required by the filesystem (if any).
        :rtype: file object

        :raises fs.errors.FileExpected: If the path is not a file.
        :raises fs.errors.FileExists: If the file exists, and
            *exclusive mode* is specified (`x` in the mode).
        :raises fs.errors.ResourceNotFound: If `path` does not exist.

        """

    @abc.abstractmethod
    def remove(self, path):
        """
        Remove a file.

        :param str path: Path to the file you want to remove.

        :raises fs.errors.FileExpected: if the path is a directory.
        :raises fs.errors.ResourceNotFound: if the path does not
            exist.

        """

    @abc.abstractmethod
    def removedir(self, path):
        """
        Remove a directory from the filesystem.

        :param str path: Path of the directory to remove.

        :raises fs.errors.DirectoryNotEmpty: If the directory is not
            empty (see :meth:`~fs.base.removetree` if you want to
            remove the directory contents).
        :raises fs.errors.DirectoryExpected: If the path is not a
            directory.
        :raises fs.errors.ResourceNotFound: If the path does not
            exist.
        :raises fs.errors.RemoveRootError: If an attempt is made to
            remove the root directory (i.e. `'/'`).
        """

    @abc.abstractmethod
    def setinfo(self, path, info):
        """
        Set info on a resource.

        :param str path: Path to a resource on the filesystem.
        :param dict info: Dict of resource info.

        :raises fs.errors.ResourceNotFound: If `path` does not exist
            on the filesystem.

        This method is the compliment to :class:`~fs.base.getinfo` and is
        used to set info values on a resource.

        The ``info`` dict should be in the same format as the raw
        info returned by ``getinfo(file).raw``. Here's an example::

            details_info = {
                "details":
                {
                    "modified_time": time.time()
                }
            }
            my_fs.setinfo('file.txt', details_info)

        """

    # ---------------------------------------------------------------- #
    # Optional methods                                                 #
    # Filesystems *may* implement these methods.                       #
    # ---------------------------------------------------------------- #

    def appendbytes(self, path, data):
        """
        Append bytes to the end of a file. Creating the file if it
        doesn't already exists.

        :param str path: Path to a file.
        :param bytes data: Bytes to append.
        :raises ValueError: if ``data`` is not bytes.
        :raises fs.errors.ResourceNotFound: if a parent directory of
            ``path`` does not exist.

        """
        if not isinstance(data, bytes):
            raise ValueError('must be bytes')
        with self._lock:
            with self.open(path, 'ab') as append_file:
                append_file.write(data)

    def appendtext(self,
                   path,
                   text,
                   encoding='utf-8',
                   errors=None,
                   newline=''):
        """
        Append text to a file. Creating the file if it doesn't already
        exists.

        :param str path: Path to a file.
        :param str text: Text to append.
        :raises ValueError: if ``text`` is not bytes.
        :raises fs.errors.ResourceNotFound: if a parent directory of
            ``path`` does not exist.

        """
        if not isinstance(text, six.text_type):
            raise ValueError('must be unicode string')
        with self._lock:
            with self.open(path,
                           'at',
                           encoding=encoding,
                           errors=errors,
                           newline=newline) as append_file:
                append_file.write(text)

    def close(self):
        """
        Close the filesystem and release any resources.

        It is important to call this method when you have finished
        working with the filesystem. Some filesystems may not finalize
        changes until they are closed (archives for example). You may
        call this method explicitly (it is safe to call close multiple
        times), or you can use the filesystem as a context manager to
        automatically close.

        Here's an example of automatically closing a filesystem::

            with OSFS('~/Desktop') as desktop_fs:
                desktop_fs.settext(
                    'note.txt',
                    "Don't forget to tape Game of Thrones"
                )

        If you attempt to use a filesystem that has been closed, a
        :class:`~fs.errors.FilesystemClosed` exception will be thrown.

        """
        self._closed = True

    def copy(self, src_path, dst_path, overwrite=False):
        """
        Copy file contents from ``src_path`` to ``dst_path``.

        :param src_path: Path of source file.
        :type src_path: str
        :param dst_path: Path to destination file.
        :type dst_path: str
        :raises fs.errors.DestinationExists: If ``dst_path`` exists,
            and overwrite == ``False``.
        :raises fs.errors.ResourceNotFound: If a parent directory of
            ``dst_path`` does not exist.

        """
        with self._lock:
            if not overwrite and self.exists(dst_path):
                raise errors.DestinationExists(dst_path)
            with closing(self.open(src_path, 'rb')) as read_file:
                self.setbinfile(dst_path, read_file)

    def copydir(self, src_path, dst_path, create=False):
        """
        Copy the contents of ``src_path`` to ``dst_path``.

        :param str src_path: Source directory.
        :param str dst_path: Destination directory.
        :param bool create: If ``True`` then ``src_path`` will be
            created if it doesn't already exist.
        :raises fs.errors.ResourceNotFound: If the destination
            directory does not exist, and ``create`` is not True.

        """
        with self._lock:
            if not create and not self.exists(dst_path):
                raise errors.ResourceNotFound(dst_path)
            copy.copy_dir(
                self,
                src_path,
                self,
                dst_path
            )

    def create(self, path, wipe=False):
        """
        Create an empty file.

        :param str path: Path to new file in filesystem.
        :param bool wipe: Truncate any existing file to 0 bytes.
        :returns: ``True`` if file was created, ``False`` if it already
            existed.
        :rtype: bool

        The default behavior is to create a new file if one doesn't
        already exist. If ``wipe == True`` an existing file will be
        truncated.

        """
        with self._lock:
            if not wipe and self.exists(path):
                return False
            with closing(self.open(path, 'wb')):
                pass
            return True

    def desc(self, path):
        """
        Return a short descriptive text regarding a path.

        :param str path: A path to a resource on the filesystem.
        :rtype: str

        """
        if not self.exists(path):
            raise errors.ResourceNotFound(path)
        try:
            syspath = self.getsyspath(path)
        except (errors.ResourceNotFound, errors.NoSysPath):
            return "{} on {}".format(path, self)
        else:
            return syspath

    def exists(self, path):
        """
        Check if a path maps to a resource.

        :param str path: Path to a resource
        :rtype: bool

        A ``path`` exists if it maps to any resource (including
        a directory).

        """
        try:
            self.getinfo(path)
        except errors.ResourceNotFound:
            return False
        else:
            return True

    def filterdir(self,
                  path,
                  files=None,
                  dirs=None,
                  exclude_dirs=None,
                  exclude_files=None,
                  namespaces=None,
                  page=None):
        """
        Get an iterator of resource info, filtered by file patterns.

        :param str path: A path to a directory on the filesystem.
        :param list files: A list of unix shell-style patterns to filter
            file names, e.g. ``['*.py']``.
        :param list dirs: A list of unix shell-style wildcards to
            filter directory names.
        :param list exclude_dirs: An optional list of patterns used to
            exclude directories
        :param list exclude_files: An optional list of patterns used to
            exclude files.
        :param list namespaces: A list of namespaces to include in
            the resource information.
        :param page: May be a tuple of ``(<start>, <end>)`` indexes to
            return an iterator of a subset of the resource info, or
            ``None`` to iterate over the entire directory. Paging a
            directory scan may be necessary for very large directories.
        :type page: tuple or None
        :return: An iterator of :class:`~fs.info.Info` objects.
        :rtype: iterator

        This method enhances :meth:`~fs.base.FS.scandir` with additional
        filtering functionality.

        """

        resources = self.scandir(path, namespaces=namespaces)
        filters = []

        def match_dir(patterns, info):
            """Pattern match info.name"""
            return info.is_file or self.match(patterns, info.name)

        def match_file(patterns, info):
            """Pattern match info.name"""
            return info.is_dir or self.match(patterns, info.name)

        def exclude_dir(patterns, info):
            """Pattern match info.name"""
            return info.is_file or not self.match(patterns, info.name)

        def exclude_file(patterns, info):
            """Pattern match info.name"""
            return info.is_dir or not self.match(patterns, info.name)

        if files:
            filters.append(partial(match_file, files))
        if dirs:
            filters.append(partial(match_dir, dirs))
        if exclude_dirs:
            filters.append(partial(exclude_dir, exclude_dirs))
        if exclude_files:
            filters.append(partial(exclude_file, exclude_files))

        if filters:
            resources = (
                info
                for info in resources
                if all(_filter(info) for _filter in filters)
            )

        iter_info = iter(resources)
        if page is not None:
            start, end = page
            iter_info = itertools.islice(iter_info, start, end)
        return iter_info

    def getbytes(self, path):
        """
        Get the contents of a file as bytes.

        :param str path: A path to a readable file on the filesystem.
        :returns: file contents
        :rtype: bytes

        :raises fs.errors.ResourceNotFound: If ``path`` does not
            exist.

        """
        with closing(self.open(path, mode='rb')) as read_file:
            contents = read_file.read()
        return contents

    def gettext(self, path, encoding=None, errors=None, newline=''):
        """
        Get the contents of a file as a string.

        :param str path: A path to a readable file on the filesystem.
        :param str encoding: Encoding to use when reading contents in
            text mode.
        :param str errors: Unicode errors parameter.
        :param str newline: Newlines parameter.
        :returns: file contents.
        :raises fs.errors.ResourceNotFound: If ``path`` does not
            exist.

        """
        with closing(
            self.open(
                path,
                mode='rt',
                encoding=encoding,
                errors=errors,
                newline=newline)
        ) as read_file:
            contents = read_file.read()
        return contents

    def getmeta(self, namespace="standard"):
        """
        Get meta information regarding a filesystem.

        :param keys: A list of keys to retrieve, or None for all keys.
        :type keys: list or None
        :param str namespace: The meta namespace (default is
            `"standard"`).
        :rtype: dict

        Meta information is associated with a *namespace* which may be
        specified with the `namespace` parameter. The default namespace,
        ``"standard"``, contains common information regarding the
        filesystem's capabilities. Some filesystems may provide other
        namespaces, which expose less common, or implementation specific
        information. If a requested namespace is not supported by
        a filesystem, then an empty dictionary will be returned.

        The ``"standard"`` namespace supports the following keys:

        =================== ============================================
        key                 Description
        ------------------- --------------------------------------------
        case_insensitive    True if this filesystem is case sensitive.
        invalid_path_chars  A string containing the characters that may
                            may not be used on this filesystem.
        max_path_length     Maximum number of characters permitted in a
                            path, or None for no limit.
        max_sys_path_length Maximum number of characters permitted in
                            a sys path, or None for no limit.
        network             True if this filesystem requires a network.
        read_only           True if this filesystem is read only.
        supports_rename     True if this filesystem supports an
                            os.rename operation.
        =================== ============================================

        .. note::
            Meta information is constant for the lifetime of the
            filesystem, and may be cached.


        """
        if namespace == 'standard':
            meta = self._meta
        else:
            meta = {}
        return meta

    def getsize(self, path):
        """
        Get the size (in bytes) of a resource.

        :param str path: A path to a resource.
        :rtype: int

        The *size* of a file is the total number of readable bytes,
        which may not reflect the exact number of bytes of reserved
        disk space (or other storage medium).

        The size of a directory is the number of bytes of overhead
        use to store the directory entry.

        """
        size = self.getdetails(path).size
        return size

    def getsyspath(self, path):
        """
        Get an *system path* to a resource.

        :param str path: A path on the filesystem.
        :rtype: str
        :raises fs.errors.NoSysPath: If there is no corresponding system path.

        A system path is one recognized by the OS, that may be used
        outside of PyFilesystem (in an application or a shell for
        example). This method will get the corresponding system path
        that would be referenced by ``path``.

        Not all filesystems have associated system paths. Network and
        memory based filesystems, for example, may not physically store
        data anywhere the OS knows about. It is also possible for some
        paths to have a system path, whereas others don't.

        If ``path`` doesn't have a system path,
        a :class:`~fs.errors.NoSysPath` exception will be thrown.

        .. note::

            A filesystem may return a system path even if no
            resource is referenced by that path -- as long as it can
            be certain what that system path would be.

        """
        raise errors.NoSysPath(path=path)

    def gettype(self, path):
        """
        Get the type of a resource.

        :param path: A path in the filesystem.
        :returns: :class:`~fs.ResourceType`

        A type of a resource is an integer that identifies the what
        the resource references. The standard type integers may be one
        of the values in the :class:`~fs.ResourceType` enumerations.

        The most common resource types, supported by virtually all
        filesystems are ``directory`` (1) and ``file`` (2), but the
        following types are also possible:

        ===================   ======
        ResourceType          value
        -------------------   ------
        unknown               0
        directory             1
        file                  2
        character             3
        block_special_file    4
        fifo                  5
        socket                6
        symlink               7
        ===================   ======

        Standard resource types are positive integers, negative values
        are reserved for implementation specific resource types.

        """
        resource_type = self.getdetails(path).type
        return resource_type

    def geturl(self, path, purpose='download'):
        """
        Get a URL to the given resource.

        :param str path: A path on the filesystem
        :param str purpose: A short string that indicates which URL to
            retrieve for the given path (if there is more than one). The
            default is `'download'`, which should return a URL that
            serves the file. Other filesystems may support other values
            for ``purpose``.
        :returns: A URL.
        :rtype: str
        :raises fs.errors.NoURL: If the path does not map to a URL.

        """
        raise errors.NoURL(path, purpose)

    def hassyspath(self, path):
        """
        Check if a path maps to a system path.

        :param str path: A path on the filesystem
        :rtype: bool

        """
        has_sys_path = True
        try:
            self.getsyspath(path)
        except errors.NoSysPath:
            has_sys_path = False
        return has_sys_path

    def hasurl(self, path, purpose='download'):
        """
        Check if a path has a corresponding URL.

        :param str path: A path on the filesystem
        :param str purpose: A purpose parameter, as given in
            :meth:`~fs.base.FS.geturl`.
        :rtype: bool

        """
        has_url = True
        try:
            self.geturl(path, purpose=purpose)
        except errors.NoURL:
            has_url = False
        return has_url

    def isclosed(self):
        """Check if the filesystem is closed."""
        return getattr(self, '_closed', False)

    def isdir(self, path):
        """Check a path exists and is a directory."""
        try:
            return self.getinfo(path).is_dir
        except errors.ResourceNotFound:
            return False

    def isempty(self, path):
        """
        Check if a directory is empty (contains no files or
        directories).

        :param str path: A directory path.
        :rtype: bool

        """
        return next(iter(self.scandir(path)), None) is None

    def isfile(self, path):
        """Check a path exists and is a file."""
        try:
            return not self.getinfo(path).is_dir
        except errors.ResourceNotFound:
            return False

    def lock(self):
        """
        Get a context manager that *locks* the filesystem.

        Locking a filesystem gives a thread exclusive access to it.
        Other threads will block until the threads with the lock has
        left the context manager. Here's how you would use it::

            with my_fs.lock():  # May block
                # code here has exclusive access to the filesystem

        It is a good idea to put a lock around any operations that you
        would like to be *atomic*. For instance if you are copying
        files, and you don't want another thread to delete or modify
        anything while the copy is in progress.

        Locking with this method is only required for code that calls
        multiple filesystem methods. Individual methods are thread safe
        already, and don't need to be locked.

        ..note ::
            This only locks at the Python level. There is nothing to
            prevent other processes from modifying the filesystem
            outside of the filesystem instance.

        """
        return self._lock

    def movedir(self, src_path, dst_path, create=False):
        """
        Move contents of directory ``src_path`` to ``dst_path``.

        :param str src_path: Path to source directory on the filesystem.
        :param str dst_path: Path to destination directory.
        :param create: If ``True``, then ``dst_path`` will be created if
            it doesn't already exist.
        :type create: bool

        """
        with self._lock:
            if not create and not self.exists(dst_path):
                raise errors.ResourceNotFound(dst_path)
            move.move_dir(
                self,
                src_path,
                self,
                dst_path
            )

    def makedirs(self, path, permissions=None, recreate=False):
        """
        Make a directory, and any missing intermediate directories.

        :param str path: Path to directory from root.
        :param bool recreate: If ``False`` (default), it is an error to
            attempt to create a directory that already exists. Set to
            `True` to allow directories to be re-created without errors.
        :param permissions: Initial permissions.
        :returns: A sub-directory filesystem.
        :rtype: :class:`~fs.subfs.SubFS`

        :raises fs.errors.DirectoryExists: if the path is already
            a directory, and ``recreate`` is False.
        :raises fs.errors.DirectoryExpected: if one of the ancestors
            in the path isn't a directory.

        """
        self.check()
        with self._lock:
            dir_paths = tools.get_intermediate_dirs(self, path)
            for dir_path in dir_paths:
                self.makedir(dir_path, permissions=permissions)

            try:
                self.makedir(path)
            except errors.DirectoryExists:
                if not recreate:
                    raise
            return self.opendir(path)

    def move(self,
             src_path,
             dst_path,
             overwrite=False):
        """
        Move a file from `src_path` to `dst_path`.

        :param str src_path: A path on the filesystem to move.
        :param str dst_path: A path on the filesystem where the source
            file will be written to.
        :param bool overwrite: If `True` destination path will be
            overwritten if it exists.
        :raises fs.errors.DestinationExists: If ``dst_path`` exists,
            and overwrite == ``False``.
        :raises fs.errors.ResourceNotFound: If a parent directory of
            ``dst_path`` does not exist.

        """

        if not overwrite and self.exists(dst_path):
            raise errors.DestinationExists(dst_path)
        if self.getmeta().get('supports_rename', False):
            try:
                src_sys_path = self.getsyspath(src_path)
                dst_sys_path = self.getsyspath(dst_path)
            except errors.NoSysPath:  # pragma: no cover
                pass
            else:
                try:
                    os.rename(src_sys_path, dst_sys_path)
                except OSError:
                    pass
                else:
                    return
        with self._lock:
            with self.open(src_path, 'rb') as read_file:
                self.setbinfile(dst_path, read_file)
            self.remove(src_path)

    def open(self,
             path,
             mode='r',
             buffering=-1,
             encoding=None,
             errors=None,
             newline='',
             **options):
        """
        Open a file.

        :param str path: A path to a file on the filesystem.
        :param str mode: Mode to open file object.
        :param int buffering: Buffering policy: ``0`` to switch
            buffering off, ``1`` to select line buffering, ``>1`` to
            select a fixed-size buffer, ``-1`` to auto-detect.
        :param str encoding: Encoding for text files (defaults to
            ``utf-8``)
        :param str errors: What to do with unicode decode errors (see
            `stdlib docs <https://docs.python.org/3/library/codecs.html#error-handlers>`_)
        :param str newline: New line parameter (See `stdlib docs
            <https://docs.python.org/3/library/functions.html#open>`_)
        :param options: Additional keyword parameters to set
            implementation specific options (if required). See
            implementation docs for details.

        :rtype: file object
        """
        validate_open_mode(mode)
        bin_mode = mode.replace('t', '')
        bin_file = self.openbin(path, mode=bin_mode, buffering=buffering)
        io_stream = iotools.make_stream(
            path,
            bin_file,
            mode=mode,
            buffering=buffering,
            encoding=encoding or 'utf-8',
            errors=errors,
            newline=newline,
            **options
        )
        return io_stream

    def opendir(self, path):
        """Get a filesystem object for a sub-directory.

        :param str path: Path to a directory on the filesystem.
        :returns: A filesystem object representing a sub-directory.
        :rtype: :class:`~fs.subfs.SubFS`
        :raises fs.errors.DirectoryExpected: If ``dst_path`` does not
            exist or is not a directory.

        """
        from .subfs import SubFS

        if not self.getbasic(path).is_dir:
            raise errors.DirectoryExpected(
                path=path
            )
        return SubFS(self, path)

    def removetree(self, dir_path):
        """
        Recursively remove the contents of a directory.

        This method is similar to :meth:`~fs.base.removedir`, but will
        remove the contents of the directory if it is not empty.

        :param str dir_path: Path to a directory on the filesystem.

        """

        _dir_path = abspath(normpath(dir_path))
        with self._lock:
            walker = walk.Walker(search="depth")
            gen_info = walker.info(self, _dir_path)
            for _path, info in gen_info:
                if info.is_dir:
                    self.removedir(_path)
                else:
                    self.remove(_path)
            if _dir_path != '/':
                self.removedir(dir_path)

    def scandir(self, path, namespaces=None, page=None):
        """
        Get an iterator of resource info.

        :param str path: A path on the filesystem
        :param list namespaces: A sequence of info namespaces.
        :param page: May be a tuple of ``(<start>, <end>)`` indexes to
            return an iterator of a subset of the resource info, or
            ``None`` to iterator the entire directory. Paging a
            directory scan may be necessary for very large directories.
        :type page: tuple or None
        :rtype: iterator

        """
        namespaces = namespaces or ()
        _path = abspath(normpath(path))

        info = (
            self.getinfo(
                join(_path, name),
                namespaces=namespaces
            )
            for name in self.listdir(path)
        )
        iter_info = iter(info)
        if page is not None:
            start, end = page
            iter_info = itertools.islice(iter_info, start, end)
        return iter_info

    def setbytes(self, path, contents):
        """
        Copy (bytes) data to a file.

        :param str path: Destination path on the filesystem.
        :param bytes contents: A bytes object with data to be written

        """
        if not isinstance(contents, bytes):
            raise ValueError('contents must be bytes')
        with closing(self.open(path, mode='wb')) as write_file:
            write_file.write(contents)

    def setbinfile(self, path, file):
        """
        Set a file to the contents of a binary file object.

        :param str path: A path on the filesystem.
        :param file: A file object open for reading in binary mode.
        :type file: file object

        This method copies bytes from an open binary file to a file on
        the filesystem. If the destination exists, it will first be
        truncated.

        Note that the file object ``file`` will *not* be closed by this
        method. Take care to close it after this method completes
        (ideally with a context manager). For example::

            with open('myfile.bin') as read_file:
                my_fs.setbinfile('myfile.bin', read_file)

        """

        with self._lock:
            with self.open(path, 'wb') as dst_file:
                tools.copy_file_data(file, dst_file)

    def setfile(self,
                path,
                file,
                encoding=None,
                errors=None,
                newline=None):
        """
        Set a file to the contents of a file object.

        :param str path: A path on the filesystem.
        :param file: A file object open for reading.
        :type file: file object
        :param str encoding: Encoding of destination file, or ``None``
            for binary.
        :param str errors: How encoding errors should be treated (same
            as ``io.open``).
        :param str newline: Newline parameter (same is ``io.open``).

        This method will read the contents of a supplied file object,
        and write to a file on the filesystem. If the destination
        exists, it will first be truncated.

        If `encoding` is supplied, the destination will be opened in
        text mode.

        Note that the file object ``file`` will *not* be closed by this
        method. Take care to close it after this method completes
        (ideally with a context manager). For example::

            with open('myfile.bin') as read_file:
                my_fs.setfile('myfile.bin', read_file)

        """
        mode = 'wb' if encoding is None else 'wt'

        with self._lock:
            with self.open(path,
                           mode=mode,
                           encoding=encoding,
                           errors=errors,
                           newline=newline) as dst_file:
                tools.copy_file_data(file, dst_file)

    def settimes(self, path, accessed=None, modified=None):
        """
        Set the accessed and modified time on a resource.

        :param accessed: The accessed time, as a datetime, or None
            to use the current rime.
        :param modified: The modified time, or ``None`` (the default) to
            use the same time as ``accessed`` parameter.

        """

        details = {}
        raw_info = {
            "details": details
        }

        details['accessed'] = (
            time.time()
            if accessed is None
            else datetime_to_epoch(accessed)
        )

        details['modified'] = (
            details['accessed']
            if modified is None
            else datetime_to_epoch(modified)
        )

        self.setinfo(path, raw_info)

    def settext(self,
                path,
                contents,
                encoding='utf-8',
                errors=None,
                newline=''):
        """
        Create or replace a file with text.

        :param str contents: Path on the filesystem.
        :param str encoding: Encoding of destination file (default
            'UTF-8).
        :param str errors: Error parameter for encoding (same as
            ``io.open``).
        :param str newline: Newline parameter for encoding (same as
            ``io.open``).

        """
        if not isinstance(contents, six.text_type):
            raise ValueError('contents must be unicode')
        with closing(self.open(path,
                               mode="wt",
                               encoding=encoding,
                               errors=errors,
                               newline=newline)) as write_file:
            write_file.write(contents)

    def touch(self, path):
        """
        Create a new file if ``path`` doesn't exist, or update accessed
        and modified times if the path does exist.

        This method is similar to the linux command of the same name.

        :param str path: A path to a file on the filesystem.

        """
        with self._lock:
            now = time.time()
            if not self.create(path):
                raw_info = {
                    "details": {
                        "accessed": now,
                        "modified": now
                    }
                }
                self.setinfo(path, raw_info)

    def validatepath(self, path):
        """
        Check if a path is valid on this filesystem, and return a
        normalized absolute path.

        Many filesystems have restrictions on the format of paths they
        support. This method will check that ``path`` is valid on the
        underlaying storage mechanism and throw a
        :class:`~fs.errors.InvalidPath` exception if it is not.

        :param str path: A path
        :returns: A normalized, absolute path.
        :rtype: str
        :raises fs.errors.InvalidPath: If the path is invalid.
        :raises fs.errors.FilesystemClosed: if the filesystem
            is closed.

        """
        self.check()

        if isinstance(path, bytes):
            raise TypeError(
                'paths must be unicode (not str)'
                if six.PY2 else
                'paths must be str (not bytes)'
            )

        meta = self.getmeta()

        invalid_chars = meta.get('invalid_path_chars')
        if invalid_chars:
            if set(path).intersection(invalid_chars):
                raise errors.InvalidCharsInPath(path)

        max_sys_path_length = meta.get('max_sys_path_length')
        if max_sys_path_length is not None:
            try:
                sys_path = self.getsyspath(path)
            except errors.NoSysPath:  # pragma: no cover
                pass
            else:
                if len(sys_path) > max_sys_path_length:
                    _msg = 'path too long '\
                        '(max {max_chars} characters in sys path)'
                    msg = _msg.format(max_chars=max_sys_path_length)
                    raise errors.InvalidPath(path, msg=msg)
        path = abspath(normpath(path))
        return path

    # ---------------------------------------------------------------- #
    # Helper methods                                                   #
    # Filesystems should not implement these methods.                  #
    # ---------------------------------------------------------------- #

    def getbasic(self, path):
        """
        Get the *basic* resource info.

        :param str path: A path on the filesystem.
        :returns: Resource information object for ``path``.
        :rtype: :class:`~fs.info.Info`

        This method is shorthand for the following::

            fs.getinfo(path, namespaces=['basic'])

        """
        return self.getinfo(path, namespaces=['basic'])

    def getdetails(self, path):
        """
        Get the *details* resource info.

        :param str path: A path on the filesystem.
        :returns: Resource information object for ``path``.
        :rtype: :class:`~fs.info.Info`

        This method is shorthand for the following::

            fs.getinfo(path, namespaces=['details'])

        """
        return self.getinfo(path, namespaces=['details'])

    def check(self):
        """
        Check a filesystem may be used.

        Will throw a :class:`~fs.errors.FilesystemClosed` if the
            filesystem is closed.

        :returns: None
        :raises fs.errors.FilesystemClosed: if the filesystem
            is closed.

        """
        if self.isclosed():
            raise errors.FilesystemClosed()

    def match(self, patterns, name):
        """
        Check if a name matches any of a list of wildcards.

        :param list patterns: A list of patterns, e.g. ``['*.py']``
        :param str name: A file or directory name (not a path)
        :rtype: bool

        If a filesystem is case *insensitive* (such as Windows) then
        this method will perform a case insensitive match (i.e. ``*.py``
        will match the same names as ``*.PY``). Otherwise the match will
        be case sensitive (``*.py`` and ``*.PY`` will match different
        names).

            >>> home_fs.match(['*.py'], '__init__.py')
            True
            >>> home_fs.match(['*.jpg', '*.png'], 'foo.gif')
            False

        If ``patterns`` is ``None``, or (``['*']``), then this method
        will always return True.

        """
        if patterns is None:
            return True
        if isinstance(patterns, six.text_type):
            raise ValueError('patterns must be a list or sequence')
        case_sensitive = self.getmeta().get('case_sensitive', True)
        matcher = wildcard.get_matcher(patterns, case_sensitive)
        return matcher(name)

    def tree(self, **kwargs):
        """
        Render a tree view of the filesystem to stdout or a file.

        The parameters are passed to :func:`~fs.tree.render`.

        """
        from .tree import render
        render(self, **kwargs)
