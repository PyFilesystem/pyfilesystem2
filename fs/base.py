"""PyFilesystem base class.

The filesystem base class is common to all filesystems. If you
familiarize yourself with this (rather straightforward) API, you
can work with any of the supported filesystems.

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
    """Base class for FS objects.
    """

    # This is the "standard" meta namespace.
    _meta = {}

    def __init__(self):
        """Create a filesystem. See help(type(self)) for accurate signature.
        """
        self._closed = False
        self._lock = threading.RLock()
        super(FS, self).__init__()

    def __enter__(self):
        """Allow use of filesystem as a context manager.
        """
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Close filesystem on exit.
        """
        self.close()

    @property
    def walk(self):
        """`~fs.walk.BoundWalker`: a walker bound to this filesystem.
        """
        return Walker.bind(self)

    # ---------------------------------------------------------------- #
    # Required methods                                                 #
    # Filesystems must implement these methods.                        #
    # ---------------------------------------------------------------- #

    @abc.abstractmethod
    def getinfo(self, path, namespaces=None):
        """Get information about a resource on a filesystem.

        Arguments:
            path (str): A path to a resource on the filesystem.
            namespaces (list, optional): Info namespaces to query
                (defaults to *basic*).

        Returns:
            ~fs.info.Info: resource information object.

        For more information regarding resource information, see :ref:`info`.

        """

    @abc.abstractmethod
    def listdir(self, path):
        """Get a list of the resource names in a directory.

        This method will return a list of the resources in a directory.
        A *resource* is a file, directory, or one of the other types
        defined in `~fs.ResourceType`.

        Arguments:
            path (str): A path to a directory on the filesystem

        Returns:
            list: list of names, relative to ``path``.

        Raises:
            fs.errors.DirectoryExpected: If ``path`` is not a directory.
            fs.errors.ResourceNotFound: If ``path`` does not exist.

        """

    @abc.abstractmethod
    def makedir(self, path, permissions=None, recreate=False):
        """Make a directory.

        Arguments:
            path (str): Path to directory from root.
            permissions (~fs.permissions.Permissions, optional): a
                `Permissions` instance, or `None` to use default.
            recreate (bool, optional): Set to `True` to avoid raising an
                error if the directory already exists (defaults to `False`).

        Returns:
            ~fs.subfs.SubFS: a filesystem whose root is the new directory.

        Raises:
            fs.errors.DirectoryExists: If the path already exists.
            fs.errors.ResourceNotFound: If the path is not found.

        """

    @abc.abstractmethod
    def openbin(self, path, mode="r", buffering=-1, **options):
        """Open a binary file-like object.

        Arguments:
            path (str): A path on the filesystem.
            mode (str, optional): Mode to open file (must be a valid
                non-text mode, defaults to *r*). Since this method only
                opens binary files, the ``b`` in the mode string is implied.s
            buffering (int, optional): Buffering policy (-1 to use
                default buffering, 0 to disable buffering, or any
                positive integer to indicate a buffer size).
            **options: keyword arguments for any additional information
                required by the filesystem (if any).

        Returns:
            io.IOBase: a *file-like* object.

        Raises:
            fs.errors.FileExpected: If the path is not a file.
            fs.errors.FileExists: If the file exists, and *exclusive mode*
                is specified (``x`` in the mode).
            fs.errors.ResourceNotFound: If the path does not exist.

        """

    @abc.abstractmethod
    def remove(self, path):
        """Remove a file from the filesystem.

        Arguments:
            path (str): Path of the file to remove.

        Raises:
            fs.errors.FileExpected: If the path is a directory.
            fs.errors.ResourceNotFound: If the path does not exist.

        """

    @abc.abstractmethod
    def removedir(self, path):
        """Remove a directory from the filesystem.

        Arguments:
            path (str): Path of the directory to remove.

        Raises:
            fs.errors.DirectoryNotEmpty: If the directory is not empty (
                see `~fs.base.FS.removetree` for a way to remove the
                directory contents.).
            fs.errors.DirectoryExpected: If the path does not refer to
                a directory.
            fs.errors.ResourceNotFound: If no resource exists at the
                given path.
            fs.errors.RemoveRootError: If an attempt is made to remove
                the root directory (i.e. ``'/'``)

        """

    @abc.abstractmethod
    def setinfo(self, path, info):
        """Set info on a resource.

        This method is the compliment to `~fs.base.FS.getinfo`
        and is used to set info values on a resource.

        Arguments:
            path (str): Path to a resource on the filesystem.
            info (dict): Dictionary of resource info.

        Raises:
            fs.errors.ResourceNotFound: If ``path`` does not exist
                on the filesystem

        The ``info`` dict should be in the same format as the raw
        info returned by ``getinfo(file).raw``.

        Example:
            >>> details_info = {"details": {
            ...     "modified_time": time.time()
            ... }}
            >>> my_fs.setinfo('file.txt', details_info)

        """

    # ---------------------------------------------------------------- #
    # Optional methods                                                 #
    # Filesystems *may* implement these methods.                       #
    # ---------------------------------------------------------------- #

    def appendbytes(self, path, data):
        """Append bytes to the end of a file, creating it if needed.

        Arguments:
            path (str): Path to a file.
            data (bytes): Bytes to append.

        Raises:
            TypeError: If ``data`` is not a `bytes` instance.
            fs.errors.ResourceNotFound: If a parent directory of
                ``path`` does not exist.

        """
        if not isinstance(data, bytes):
            raise TypeError('must be bytes')
        with self._lock:
            with self.open(path, 'ab') as append_file:
                append_file.write(data)

    def appendtext(self,
                   path,
                   text,
                   encoding='utf-8',
                   errors=None,
                   newline=''):
        """Append text to the end of a file, creating it if needed.

        Arguments:
            path (str): Path to a file.
            text (str): Text to append.
            encoding (str, optional): Encoding for text files
                (defaults to ``utf-8``).
            errors (str, optional): What to do with unicode decode errors
                (see `codecs` module for more information).
            newline (str, optional): Newline parameter.

        Raises:
            TypeError: if ``text`` is not an unicode string.
            fs.errors.ResourceNotFound: if a parent directory of
                ``path`` does not exist.

        """
        if not isinstance(text, six.text_type):
            raise TypeError('must be unicode string')
        with self._lock:
            with self.open(path,
                           'at',
                           encoding=encoding,
                           errors=errors,
                           newline=newline) as append_file:
                append_file.write(text)

    def close(self):
        """Close the filesystem and release any resources.

        It is important to call this method when you have finished
        working with the filesystem. Some filesystems may not finalize
        changes until they are closed (archives for example). You may
        call this method explicitly (it is safe to call close multiple
        times), or you can use the filesystem as a context manager to
        automatically close.

        Example:
            >>> with OSFS('~/Desktop') as desktop_fs:
            ...    desktop_fs.settext(
            ...        'note.txt',
            ...        "Don't forget to tape Game of Thrones"
            ...    )

        If you attempt to use a filesystem that has been closed, a
        `~fs.errors.FilesystemClosed` exception will be thrown.

        """
        self._closed = True

    def copy(self, src_path, dst_path, overwrite=False):
        """Copy file contents from ``src_path`` to ``dst_path``.

        Arguments:
            src_path (str): Path of source file.
            dst_path (str): Path to destination file.
            overwrite (bool, Optional): If `True`, overwrite the
                destination file if it exists (defaults to `False`).

        Raises:
            fs.errors.DestinationExists: If ``dst_path`` exists,
                and ``overwrite`` is `False`.
            fs.errors.ResourceNotFound: If a parent directory of
                ``dst_path`` does not exist.

        """
        with self._lock:
            if not overwrite and self.exists(dst_path):
                raise errors.DestinationExists(dst_path)
            with closing(self.open(src_path, 'rb')) as read_file:
                self.setbinfile(dst_path, read_file)

    def copydir(self, src_path, dst_path, create=False):
        """Copy the contents of ``src_path`` to ``dst_path``.

        Arguments:
            src_path (str): Path of source directory.
            dst_path (str): Path to destination directory.
            create (bool, optional): If `True`, then ``dst_path``
                will be created if it doesn't exist alreadys
                (defaults to `False`).

        Raises:
            fs.errors.ResourceNotFound: If the ``dst_path``
                does not exist, and ``create`` is not `True`.

        """
        with self._lock:
            if not create and not self.exists(dst_path):
                raise errors.ResourceNotFound(dst_path)
            if not self.getinfo(src_path).is_dir:
                raise errors.DirectoryExpected(src_path)
            copy.copy_dir(
                self,
                src_path,
                self,
                dst_path
            )

    def create(self, path, wipe=False):
        """Create an empty file.

        The default behavior is to create a new file if one doesn't
        already exist. If ``wipe`` is `True`, any existing file will
        be truncated.

        Arguments:
            path (str): Path to a new file in the filesystem.
            wipe (bool, optional): If `True`, truncate any existing
                file to 0 bytes (defaults to `False`).

        Returns:
            bool: `True` if a new file had to be created.

        """
        with self._lock:
            if not wipe and self.exists(path):
                return False
            with closing(self.open(path, 'wb')):
                pass
            return True

    def desc(self, path):
        """Return a short descriptive text regarding a path.

        Arguments:
            path (str): A path to a resource on the filesystem.

        Returns:
            str: a short description of the path.

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
        """Check if a path maps to a resource.

        Arguments:
            path (str): Path to a resource.

        Returns:
            bool: `True` if a resource exists at the given path.

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
        """Get an iterator of resource info, filtered by patterns.

        This method enhances `~fs.base.FS.scandir` with additional
        filtering functionality.

        Arguments:
            path (str): A path to a directory on the filesystem.
            files (list, optional): A list of UNIX shell-style patterns
                to filter file names, e.g. ``['*.py']``.
            dirs (list, optional): A list of UNIX shell-style patterns
                to filter directory names.
            exclude_dirs (list, optional): An optional list of patterns
                used to exclude directories.
            exclude_files (list, optional): An optional list of patterns
                used to exclude files.
            namespaces (list, optional): A list of namespaces to include
                in the resource information, e.g. ``['basic', 'access']``.
            page (tuple, optional): May be a tuple of ``(<start>, <end>)``
                indexes to return an iterator of a subset of the resource
                info, or `None` to iterate over the entire directory.
                Paging a directory scan may be necessary for very large
                directories.

        Returns:
            ~collections.abc.Iterator: an iterator of `Info` objects.

        """
        resources = self.scandir(path, namespaces=namespaces)
        filters = []

        def match_dir(patterns, info):
            """Pattern match info.name.
            """
            return info.is_file or self.match(patterns, info.name)

        def match_file(patterns, info):
            """Pattern match info.name.
            """
            return info.is_dir or self.match(patterns, info.name)

        def exclude_dir(patterns, info):
            """Pattern match info.name.
            """
            return info.is_file or not self.match(patterns, info.name)

        def exclude_file(patterns, info):
            """Pattern match info.name.
            """
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
        """Get the contents of a file as bytes.

        Arguments:
            path (str): A path to a readable file on the filesystem.

        Returns:
            bytes: the file contents.

        Raises:
            fs.errors.ResourceNotFound: if ``path`` does not exist.

        """
        with closing(self.open(path, mode='rb')) as read_file:
            contents = read_file.read()
        return contents

    def gettext(self, path, encoding=None, errors=None, newline=''):
        """Get the contents of a file as a string.

        Arguments:
            path (str): A path to a readable file on the filesystem.
            encoding (str, optional): Encoding to use when reading contents
                in text mode (defaults to `None`, reading in binary mode).
            errors (str, optional): Unicode errors parameter.
            newline (str, optional): Newlines parameter.

        Returns:
            str: file contents.

        Raises:
            fs.errors.ResourceNotFound: If ``path`` does not exist.

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
        """Get meta information regarding a filesystem.

        Arguments:
            namespace (str, optional): The meta namespace
                (defaults to ``"standard"``).

        Returns:
            dict: the meta information.

        Meta information is associated with a *namespace* which may be
        specified with the ``namespace`` parameter. The default namespace,
        ``"standard"``, contains common information regarding the
        filesystem's capabilities. Some filesystems may provide other
        namespaces which expose less common or implementation specific
        information. If a requested namespace is not supported by
        a filesystem, then an empty dictionary will be returned.

        The ``"standard"`` namespace supports the following keys:

        =================== ============================================
        key                 Description
        ------------------- --------------------------------------------
        case_insensitive    `True` if this filesystem is case
                            insensitive.
        invalid_path_chars  A string containing the characters that
                            may not be used on this filesystem.
        max_path_length     Maximum number of characters permitted in
                            a path, or `None` for no limit.
        max_sys_path_length Maximum number of characters permitted in
                            a sys path, or `None` for no limit.
        network             `True` if this filesystem requires a
                            network.
        read_only           `True` if this filesystem is read only.
        supports_rename     `True` if this filesystem supports an
                            `os.rename` operation.
        =================== ============================================

        Most builtin filesystems will provide all these keys, and third-
        party filesystems should do so whenever possible, but a key may
        not be present if there is no way to know the value.

        Note:
            Meta information is constant for the lifetime of the
            filesystem, and may be cached.

        """
        if namespace == 'standard':
            meta = self._meta.copy()
        else:
            meta = {}
        return meta

    def getsize(self, path):
        """Get the size (in bytes) of a resource.

        Arguments:
            path (str): A path to a resource.

        Returns:
            int: the *size* of the resource.

        The *size* of a file is the total number of readable bytes,
        which may not reflect the exact number of bytes of reserved
        disk space (or other storage medium).

        The size of a directory is the number of bytes of overhead
        use to store the directory entry.

        """
        size = self.getdetails(path).size
        return size

    def getsyspath(self, path):
        """Get the *system path* of a resource.

        Parameters:
            path (str): A path on the filesystem.

        Returns:
            str: the *system path* of the resource, if any.

        Raises:
            fs.errors.NoSysPath: If there is no corresponding system path.

        A system path is one recognized by the OS, that may be used
        outside of PyFilesystem (in an application or a shell for
        example). This method will get the corresponding system path
        that would be referenced by ``path``.

        Not all filesystems have associated system paths. Network and
        memory based filesystems, for example, may not physically store
        data anywhere the OS knows about. It is also possible for some
        paths to have a system path, whereas others don't.

        If ``path`` doesn't have a system path, a `~fs.errors.NoSysPath`
        exception will be thrown.

        Note:
            A filesystem may return a system path even if no
            resource is referenced by that path -- as long as it can
            be certain what that system path would be.

        """
        raise errors.NoSysPath(path=path)

    def gettype(self, path):
        """Get the type of a resource.

        Parameters:
            path (str): A path on the filesystem.

        Returns:
            ~fs.ResourceType: the type of the resource.

        A type of a resource is an integer that identifies the what
        the resource references. The standard type integers may be one
        of the values in the `~fs.ResourceType` enumerations.

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
        """Get the URL to a given resource.

        Parameters:
            path (str): A path on the filesystem
            purpose (str, optional): A short string that indicates which
                URL to retrieve for the given path (if there is more
                than one). The default is ``'download'``, which should
                return a URL that serves the file. Other filesystems may
                support other values for ``purpose``.

        Returns:
            str: a URL.

        Raises:
            fs.errors.NoURL: If the path does not map to a URL.

        """
        raise errors.NoURL(path, purpose)

    def hassyspath(self, path):
        """Check if a path maps to a system path.

        Parameters:
            path (str): A path on the filesystem.

        Returns:
            bool: `True` if the resource at ``path`` has a *syspath*.

        """
        has_sys_path = True
        try:
            self.getsyspath(path)
        except errors.NoSysPath:
            has_sys_path = False
        return has_sys_path

    def hasurl(self, path, purpose='download'):
        """Check if a path has a corresponding URL.

        Parameters:
            path (str): A path on the filesystem.
            purpose (str, optional): A purpose parameter, as given in
                `~fs.base.FS.geturl`.

        Returns:
            bool: `True` if an URL for the given purpose exists.

        """
        has_url = True
        try:
            self.geturl(path, purpose=purpose)
        except errors.NoURL:
            has_url = False
        return has_url

    def isclosed(self):
        """Check if the filesystem is closed.
        """
        return getattr(self, '_closed', False)

    def isdir(self, path):
        """Check if a path maps to an existing directory.

        Parameters:
            path (str): A path on the filesystem.

        Returns:
            bool: `True` if ``path`` maps to a directory.

        """
        try:
            return self.getinfo(path).is_dir
        except errors.ResourceNotFound:
            return False

    def isempty(self, path):
        """Check if a directory is empty.

        A directory is considered empty when it does not contain
        any file or any directory.

        Parameters:
            path (str): A path to a directory on the filesystem.

        Returns:
            bool: `True` if the directory is empty.

        Raises:
            errors.DirectoryExpected: If ``path`` is not a directory.
            errors.ResourceNotFound: If ``path`` does not exist.

        """
        return next(iter(self.scandir(path)), None) is None

    def isfile(self, path):
        """Check if a path maps to an existing file.

        Parameters:
            path (str): A path on the filesystem.

        Returns:
            bool: `True` if ``path`` maps to a file.

        """
        try:
            return not self.getinfo(path).is_dir
        except errors.ResourceNotFound:
            return False

    def islink(self, path):
        """Check if a path maps to a symlink.

        Parameters:
            path (str): A path on the filesystem.

        Returns:
            bool: `True` if ``path`` maps to a symlink.

        """
        self.getinfo(path)
        return False

    def lock(self):
        """Get a context manager that *locks* the filesystem.

        Locking a filesystem gives a thread exclusive access to it.
        Other threads will block until the threads with the lock has
        left the context manager.

        Returns:
            threading.RLock: a lock specific to the filesystem instance.

        Example:
            >>> with my_fs.lock():  # May block
            ...    # code here has exclusive access to the filesystem

        It is a good idea to put a lock around any operations that you
        would like to be *atomic*. For instance if you are copying
        files, and you don't want another thread to delete or modify
        anything while the copy is in progress.

        Locking with this method is only required for code that calls
        multiple filesystem methods. Individual methods are thread safe
        already, and don't need to be locked.

        Note:
            This only locks at the Python level. There is nothing to
            prevent other processes from modifying the filesystem
            outside of the filesystem instance.

        """
        return self._lock

    def movedir(self, src_path, dst_path, create=False):
        """Move contents of directory ``src_path`` to ``dst_path``.

        Parameters:
            src_path (str): Path of source directory on the filesystem.
            dst_path (str): Path to destination directory.
            create (bool, optional): If `True`, then ``dst_path`` will
                be created if it doesn't exist already (defaults
                to `False`).

        Raises:
            fs.errors.ResourceNotFound: if ``dst_path`` does not exist,
                and ``create`` is `False`.

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
        """Make a directory, and any missing intermediate directories.

        Arguments:
            path (str): Path to directory from root.
            permissions (~fs.permissions.Permissions, optional): Initial
                permissions, or `None` to use defaults.
            recreate (bool, optional):  If `False` (the default),
                attempting to create an existing directory will raise an
                error. Set to `True` to ignore existing directories.

        Returns:
            ~fs.subfs.SubFS: A sub-directory filesystem.

        Raises:
            fs.errors.DirectoryExists: if the path is already
                a directory, and ``recreate`` is `False`.
            fs.errors.DirectoryExpected: if one of the ancestors
                in the path is not a directory.

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
        """Move a file from ``src_path`` to ``dst_path``.

        Arguments:
            src_path (str): A path on the filesystem to move.
            dst_path (str): A path on the filesystem where the source
                file will be written to.
            overwrite (bool, optional): If `True`, destination path
                will be overwritten if it exists.

        Raises:
            fs.errors.FileExpected: If ``src_path`` maps to a
                directory instead of a file.
            fs.errors.DestinationExists: If ``dst_path`` exists,
                and ``overwrite`` is `False`.
            fs.errors.ResourceNotFound: If a parent directory of
                ``dst_path`` does not exist.

        """
        if not overwrite and self.exists(dst_path):
            raise errors.DestinationExists(dst_path)
        if self.getinfo(src_path).is_dir:
            raise errors.FileExpected(src_path)
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
        """Open a file.

        Arguments:
            path (str): A path to a file on the filesystem.
            mode (str, optional): Mode to open the file object with
                (defaults to *r*).
            buffering (int, optional): Buffering policy (-1 to use
                default buffering, 0 to disable buffering, 1 to select
                line buffering, of any positive integer to indicate
                a buffer size).
            encoding (str, optional): Encoding for text files
                (defaults to ``utf-8``)
            errors (str, optional): What to do with unicode decode errors
                (see `codecs` module for more information).
            newline (str, optional): Newline parameter.
            **options: keyword arguments for any additional information
                required by the filesystem (if any).

        Returns:
            io.IOBase: a *file-like* object.

        Raises:
            fs.errors.FileExpected: If the path is not a file.
            fs.errors.FileExists: If the file exists, and *exclusive mode*
                is specified (``x`` in the mode).
            fs.errors.ResourceNotFound: If the path does not exist.

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

    def opendir(self, path, factory=None):
        """Get a filesystem object for a sub-directory.

        Arguments:
            path (str): Path to a directory on the filesystem.
            factory (callable, optional): A callable that when invoked
                with an FS instance and ``path`` will return a new FS object
                representing the sub-directory contents. If no ``factory``
                is supplied then `~fs.subfs.SubFS` will be used.

        Returns:
            ~fs.subfs.SubFS: A filesystem representing a sub-directory.

        Raises:
            fs.errors.DirectoryExpected: If ``dst_path`` does not
                exist or is not a directory.

        """
        from .subfs import SubFS
        factory = factory or SubFS

        if not self.getbasic(path).is_dir:
            raise errors.DirectoryExpected(
                path=path
            )
        return factory(self, path)

    def removetree(self, dir_path):
        """Recursively remove the contents of a directory.

        This method is similar to `~fs.base.removedir`, but will
        remove the contents of the directory if it is not empty.

        Arguments:
            dir_path (str): Path to a directory on the filesystem.

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
        """Get an iterator of resource info.

        Arguments:
            path (str): A path to a directory on the filesystem.
            namespaces (list, optional): A list of namespaces to include
                in the resource information, e.g. ``['basic', 'access']``.
            page (tuple, optional): May be a tuple of ``(<start>, <end>)``
                indexes to return an iterator of a subset of the resource
                info, or `None` to iterate over the entire directory.
                Paging a directory scan may be necessary for very large
                directories.

        Returns:
            ~collections.abc.Iterator: an iterator of `Info` objects.

        Raises:
            fs.errors.DirectoryExpected: If ``path`` is not a directory.
            fs.errors.ResourceNotFound: If ``path`` does not exist.

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
        """Copy binary data to a file.

        Arguments:
            path (str): Destination path on the filesystem.
            contents (bytes): Data to be written.

        Raises:
            TypeError: if contents is not bytes.

        """
        if not isinstance(contents, bytes):
            raise TypeError('contents must be bytes')
        with closing(self.open(path, mode='wb')) as write_file:
            write_file.write(contents)

    def setbinfile(self, path, file):
        """Set a file to the contents of a binary file object.

        This method copies bytes from an open binary file to a file on
        the filesystem. If the destination exists, it will first be
        truncated.

        Arguments:
            path (str): A path on the filesystem.
            file (io.IOBase): a file object open for reading in
                binary mode.

        Note that the file object ``file`` will *not* be closed by this
        method. Take care to close it after this method completes
        (ideally with a context manager).

        Example:
            >>> with open('myfile.bin') as read_file:
            ...     my_fs.setbinfile('myfile.bin', read_file)

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
        """Set a file to the contents of a file object.

        Arguments:
            path (str): A path on the filesystem.
            file (io.IOBase): A file object open for reading.
            encoding (str, optional): Encoding of destination file,
                defaults to `None` for binary.
            errors (str, optional): How encoding errors should be treated
                (same as `io.open`).
            newline (str, optional): Newline parameter (same
                as `io.open`).

        This method will read the contents of a supplied file object,
        and write to a file on the filesystem. If the destination
        exists, it will first be truncated.

        If ``encoding`` is supplied, the destination will be opened in
        text mode.

        Note that the file object ``file`` will *not* be closed by this
        method. Take care to close it after this method completes
        (ideally with a context manager).

        Example:
            >>> with open('myfile.bin') as read_file:
            ...     my_fs.setfile('myfile.bin', read_file)

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
        """Set the accessed and modified time on a resource.

        Arguments:
            path: A path to a resource on the filesystem.
            accessed (datetime, optional): The accessed time, or
                `None` (the default) to use the current time.
            modified (datetime, optional): The modified time, or
                `None` (the default) to use the same time as the
                ``accessed`` parameter.

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
        """Create or replace a file with text.

        Arguments:
            contents (str): A path on the filesystem.
            encoding (str, optional): Encoding of destination file
                (defaults to ``'ut-8'``).
            errors (str, optional): How encoding errors should be treated
                (same as `io.open`).
            newline (str, optional): Newline parameter (same
                as `io.open`).

        Raises:
            TypeError: if ``contents`` is not a unicode string.

        """
        if not isinstance(contents, six.text_type):
            raise TypeError('contents must be unicode')
        with closing(self.open(path,
                               mode="wt",
                               encoding=encoding,
                               errors=errors,
                               newline=newline)) as write_file:
            write_file.write(contents)

    def touch(self, path):
        """Touch a file on the filesystem.

        Touching a file means creating a new file if ``path`` doesn't
        exist, or update accessed and modified times if the path does
        exist. This method is similar to the linux command of the same
        name.

        Arguments:
            path (str): A path to a file on the filesystem.

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
        """Check if a path is valid, returning a normalized absolute
        path.

        Many filesystems have restrictions on the format of paths they
        support. This method will check that ``path`` is valid on the
        underlaying storage mechanism and throw a
        `~fs.errors.InvalidPath` exception if it is not.

        Arguments:
            path (str): A path.

        Returns:
            str: A normalized, absolute path.

        Raises:
            fs.errors.InvalidCharsInPath: If the path contains
                invalid characters.
            fs.errors.InvalidPath: If the path is invalid.
            fs.errors.FilesystemClosed: if the filesystem
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
        """Get the *basic* resource info.

        This method is shorthand for the following::

            fs.getinfo(path, namespaces=['basic'])

        Arguments:
            path (str): A path on the filesystem.

        Returns:
            ~fs.info.Info: Resource information object for ``path``.

        """
        return self.getinfo(path, namespaces=['basic'])

    def getdetails(self, path):
        """Get the *details* resource info.

        This method is shorthand for the following::

            fs.getinfo(path, namespaces=['details'])

        Arguments:
            path (str): A path on the filesystem.

        Returns:
            ~fs.info.Info: Resource information object for ``path``.

        """
        return self.getinfo(path, namespaces=['details'])

    def check(self):
        """Check if a filesystem may be used.

        Raises:
            fs.errors.FilesystemClosed: if the filesystem is closed.

        """
        if self.isclosed():
            raise errors.FilesystemClosed()

    def match(self, patterns, name):
        """Check if a name matches any of a list of wildcards.

        Arguments:
            patterns (list): A list of patterns, e.g. ``['*.py']``
            name (str): A file or directory name (not a path)

        Returns:
            bool: `True` if ``name`` matches any of the patterns.

        If a filesystem is case *insensitive* (such as Windows) then
        this method will perform a case insensitive match (i.e. ``*.py``
        will match the same names as ``*.PY``). Otherwise the match will
        be case sensitive (``*.py`` and ``*.PY`` will match different
        names).

        Example:
            >>> home_fs.match(['*.py'], '__init__.py')
            True
            >>> home_fs.match(['*.jpg', '*.png'], 'foo.gif')
            False

        Note:
            If ``patterns`` is `None` (or ``['*']``), then this
            method will always return `True`.

        """
        if patterns is None:
            return True
        if isinstance(patterns, six.text_type):
            raise TypeError('patterns must be a list or sequence')
        case_sensitive = self.getmeta().get('case_sensitive', True)
        matcher = wildcard.get_matcher(patterns, case_sensitive)
        return matcher(name)

    def tree(self, **kwargs):
        """Render a tree view of the filesystem to stdout or a file.

        The parameters are passed to :func:`~fs.tree.render`.

        Keyword Arguments:
            path (str): The path of the directory to start rendering
                from (defaults to root folder, i.e. ``'/'``).
            file (io.IOBase): An open file-like object to render the
                tree, or `None` for stdout.
            encoding (str): Unicode encoding, or `None` to
                auto-detect.
            max_levels (int): Maximum number of levels to
                display, or `None` for no maximum.
            with_color (bool): Enable terminal color output,
                or `None` to auto-detect terminal.
            dirs_first (bool): Show directories first.
            exclude (list): Option list of directory patterns
                to exclude from the tree render.
            filter (list): Optional list of files patterns to
                match in the tree render.

        """
        from .tree import render
        render(self, **kwargs)
