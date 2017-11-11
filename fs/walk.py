"""Machinery for walking a filesystem.

*Walking* a filesystem means recursively visiting a directory and
any sub-directories. It is a fairly common requirement for copying,
searching etc. See :ref:`walking` for details.
"""

from __future__ import unicode_literals

import itertools

from collections import deque
from collections import namedtuple

import six

from ._repr import make_repr
from .errors import FSError
from .path import abspath
from .path import join
from .path import normpath


Step = namedtuple('Step', 'path, dirs, files')
"""type: a *step* in a directory walk.
"""


class WalkerBase(object):
    """The base class for a Walker.

    To create a custom walker, implement `~fs.walk.WalkerBase.walk`
    in a sub-class.

    See `~fs.walk.Walker` for a fully featured walker object that
    should be adequate for all but your most exotic directory walking
    needs.

    """

    def walk(self, fs, path='/', namespaces=None):
        """Walk the directory structure of a filesystem.

        Arguments:
            fs (FS): A filesystem instance.
            path (str, optional): A path to a directory on the filesystem.
            namespaces(list, optional): A list of additional namespaces
                to add to the `~fs.info.Info` objects.

        Returns:
            ~collections.Iterator: iterator of `~fs.walk.Step` named tuples.

        """
        raise NotImplementedError

    def files(self, fs, path='/'):
        """Walk a filesystem, yielding absolute paths to files.

        Arguments:
            fs (FS): A filesystem instance.
            path (str, optional): A path to a directory on the filesystem.

        Yields:
            str: absolute path to files on the filesystem found
            recursively within the given directory.

        """
        iter_walk = iter(self.walk(fs, path=path))
        for _path, _, files in iter_walk:
            for info in files:
                yield join(_path, info.name)

    def dirs(self, fs, path='/'):
        """Walk a filesystem, yielding absolute paths to directories.

        Arguments:
            fs (FS): A filesystem instance.
            path (str, optional): A path to a directory on the filesystem.

        Yields:
            str: absolute path to directories on the filesystem found
            recursively within the given directory.

        """
        for path, dirs, _ in self.walk(fs, path=path):
            for info in dirs:
                yield join(path, info.name)

    def info(self, fs, path='/', namespaces=None):
        """Walk a filesystem, yielding tuples of ``(<path>, <info>)``.

        Arguments:
            fs (FS): A filesystem instance.
            path (str, optional): A path to a directory on the filesystem.
            namespaces (list, optional): A list of additional namespaces
                to add to the `Info` objects.

        Yields:
            (str, Info): a tuple of ``(<absolute path>, <resource info>)``.

        """
        _walk = self.walk(fs, path=path, namespaces=namespaces)
        for _path, dirs, files in _walk:
            for info in itertools.chain(dirs, files):
                yield join(_path, info.name), info


class Walker(WalkerBase):
    """A walker object recursively lists directories in a filesystem.

    Arguments:
        ignore_errors (bool, optional): If `True`, any errors reading
            a directory will be ignored, otherwise exceptions will be
            raised.
        on_error (callable, optional): If ``ignore_errors`` is `False`,
            then this callable will be invoked for a path and the exception
            object. It should return `True` to ignore the error, or `False`
            to re-raise it.
        search (str, optional): If ``'breadth'`` then the directory will be
            walked *top down*. Set to ``'depth'`` to walk *bottom up*.
        filter (list, optional): If supplied, this parameter should be a
            list of filename patterns, e.g. ``['*.py']``. Files will only
            be returned if the final component matches one of the patterns.
        exclude_dirs (list, optional): A list of patterns that will be used
            to filter out directories from the walk. e.g. ``['*.svn', '*.git']``.
        max_depth (int, optional): Maximum directory depth to walk.

    """

    def __init__(self,
                 ignore_errors=False,
                 on_error=None,
                 search="breadth",
                 filter=None,
                 exclude_dirs=None,
                 max_depth=None):
        if search not in ('breadth', 'depth'):
            raise ValueError("search must be 'breadth' or 'depth'")
        self.ignore_errors = ignore_errors
        if on_error:
            if ignore_errors:
                raise ValueError(
                    'on_error is invalid when ignore_errors==True'
                )
        else:
            on_error = (
                self._ignore_errors
                if ignore_errors
                else self._raise_errors
            )
        if not callable(on_error):
            raise TypeError('on_error must be callable')

        self.on_error = on_error
        self.search = search
        self.filter = filter
        self.exclude_dirs = exclude_dirs
        self.max_depth = max_depth
        super(Walker, self).__init__()

    @classmethod
    def _ignore_errors(cls, path, error):
        """Default on_error callback."""
        return True

    @classmethod
    def _raise_errors(cls, path, error):
        """Callback to re-raise dir scan errors."""
        return False

    @classmethod
    def _calculate_depth(cls, path):
        """Calculate the 'depth' of a directory path (number of
        components).
        """
        _path = path.strip('/')
        return _path.count('/') + 1 if _path else 0

    @classmethod
    def bind(cls, fs):
        """Bind a `Walker` instance to a given filesystem.

        This *binds* in instance of the Walker to a given filesystem, so
        that you won't need to explicitly provide the filesystem as a
        parameter.

        Arguments:
            fs (FS): A filesystem object.

        Returns:
            ~fs.walk.BoundWalker: a bound walker.

        Example:
            >>> from fs import open_fs
            >>> from fs.walk import Walker
            >>> home_fs = open_fs('~/')
            >>> walker = Walker.bind(home_fs)
            >>> for path in walker.files(filter=['*.py']):
            ...     print(path)

        Unless you have written a customized walker class, you will be
        unlikely to need to call this explicitly, as filesystem objects
        already have a ``walk`` attribute which is a bound walker
        object.

        Example:
            >>> from fs import open_fs
            >>> home_fs = open_fs('~/')
            >>> for path in home_fs.walk.files(filter=['*.py']):
            ...     print(path)

        """
        return BoundWalker(fs)

    def __repr__(self):
        return make_repr(
            self.__class__.__name__,
            ignore_errors=(self.ignore_errors, False),
            on_error=(self.on_error, None),
            search=(self.search, 'breadth'),
            filter=(self.filter, None),
            exclude_dirs=(self.exclude_dirs, None),
            max_depth=(self.max_depth, None)
        )

    def filter_files(self, fs, infos):
        """Filter a sequence of resource `Info` objects.

        The default implementation filters those files for which
        `~fs.walk.Walker.check_file` returns `True`.

        Arguments:
            fs (FS): a filesystem instance.
            infos (list): A list of `~fs.info.Info` instances.

        Returns:
            list: a list of `Info` objects passing the ``check_file``
            validation.

        """
        _check_file = self.check_file
        return [
            info for info in infos
            if _check_file(fs, info)
        ]

    def _check_open_dir(self, fs, path, info):
        """Check if a directory should be considered in the walk.
        """
        if (self.exclude_dirs is not None and
            fs.match(self.exclude_dirs, info.name)):
            return False
        return self.check_open_dir(fs, path, info)

    def check_open_dir(self, fs, path, info):
        """Check if a directory should be opened.

        Override to exclude directories from the walk.

        Arguments:
            fs (FS): A filesystem instance.
            path (str): Path to directory.
            info (Info): A resource info object for the directory.

        Returns:
            bool: `True` if the directory should be opened.

        """
        return True

    def _check_scan_dir(self, fs, path, info, depth):
        """Check if a directory contents should be scanned."""
        if self.max_depth is not None and depth >= self.max_depth:
            return False
        return self.check_scan_dir(fs, path, info)

    def check_scan_dir(self, fs, path, info):
        """Check if a directory should be scanned.

        Override to omit scanning of certain directories. If a directory
        is omitted, it will appear in the walk but its files and
        sub-directories will not.

        Arguments:
            fs (FS): A filesystem instance.
            path (str): Path to directory.
            info (Info): A resource info object for the directory.

        Returns:
            bool: `True` if the directory should be scanned.

        """
        return True

    def check_file(self, fs, info):
        """Check if a filename should be included.

        Override to exclude files from the walk.

        Arguments:
            fs (FS): A filesystem instance.
            info (Info): A resource info object.

        Returns:
            bool: `True` if the file should be included.

        """
        return fs.match(self.filter, info.name)

    def _scan(self, fs, dir_path, namespaces):
        """Get an iterator of `Info` objects for a directory path.

        Arguments:
            fs (FS): A filesystem instance.
            dir_path (str): A path to a directory on the filesystem.
            namespaces (list): A list of additional namespaces to
                include in the `Info` objects.

        Returns:
            ~collections.Iterator: iterator of `Info` objects for
            resources within the given path.

        """
        try:
            for info in fs.scandir(dir_path, namespaces=namespaces):
                yield info
        except FSError as error:
            if not self.on_error(dir_path, error):
                six.reraise(type(error), error)

    def walk(self, fs, path='/', namespaces=None):
        """Walk the directory structure of a filesystem.

        Arguments:
            fs (FS): A filesystem instance.
            path (str, optional): A path to a directory on the filesystem.
            namespaces (list, optional): A list of additional namespaces
                to add to the `Info` objects.

        Returns:
            collections.Iterator: an iterator of `~fs.walk.Step` instances.

        The return value is an iterator of ``(<path>, <dirs>, <files>)``
        named tuples,  where ``<path>`` is an absolute path to a
        directory, and ``<dirs>`` and ``<files>`` are a list of
        `~fs.info.Info` objects for directories and files in ``<path>``.

        Example:
            >>> home_fs = open_fs('~/')
            >>> walker = Walker(filter=['*.py'])
            >>> namespaces = ['details']
            >>> for path, dirs, files in walker.walk(home_fs, namespaces)
            ...    print("[{}]".format(path))
            ...    print("{} directories".format(len(dirs)))
            ...    total = sum(info.size for info in files)
            ...    print("{} bytes {}".format(total))

        """
        _path = abspath(normpath(path))

        if self.search == 'breadth':
            do_walk = self._walk_breadth
        elif self.search == 'depth':
            do_walk = self._walk_depth

        return do_walk(fs, _path, namespaces=namespaces)

    def _walk_breadth(self, fs, path, namespaces=None):
        """Walk files using a *breadth first* search.
        """
        queue = deque([path])
        push = queue.appendleft
        pop = queue.pop
        depth = self._calculate_depth(path)

        while queue:
            dir_path = pop()
            dirs = []
            files = []
            for info in self._scan(fs, dir_path, namespaces=namespaces):
                if info.is_dir:
                    _depth = self._calculate_depth(dir_path) - depth + 1
                    if self._check_open_dir(fs, dir_path, info):
                        dirs.append(info)
                        if self._check_scan_dir(fs, dir_path, info, _depth):
                            push(join(dir_path, info.name))
                else:
                    files.append(info)
            yield Step(
                dir_path,
                dirs,
                self.filter_files(fs, files)
            )

    def _walk_depth(self, fs, path, namespaces=None):
        """Walk files using a *depth first* search.
        """
        # No recursion!

        def scan(path):
            """Perform scan."""
            return self._scan(fs, path, namespaces=namespaces)

        depth = self._calculate_depth(path)
        stack = [(
            path, scan(path), [], []
        )]
        push = stack.append

        while stack:
            dir_path, iter_files, dirs, files = stack[-1]
            try:
                info = next(iter_files)
            except StopIteration:
                yield Step(
                    dir_path,
                    dirs,
                    self.filter_files(fs, files)
                )
                del stack[-1]
            else:
                if info.is_dir:
                    _depth = self._calculate_depth(dir_path) - depth + 1
                    if self._check_open_dir(fs, dir_path, info):
                        dirs.append(info)
                        if self._check_scan_dir(fs, dir_path, info, _depth):
                            _path = join(dir_path, info.name)
                            push((
                                _path, scan(_path), [], []
                            ))
                else:
                    files.append(info)


class BoundWalker(object):
    """A class that binds a `Walker` instance to a `FS` instance.

    Arguments:
        fs (FS): A filesystem instance.
        walker_class (type, optional): A `~fs.walk.WalkerBase`
            sub-class. The default uses `~fs.walk.Walker`.

    You will typically not need to create instances of this class
    explicitly. Filesystems have a `~FS.walk` property which returns a
    `BoundWalker` object.

    Example:
        >>> import fs
        >>> home_fs = fs.open_fs('~/')
        >>> home_fs.walk
        BoundWalker(OSFS('/Users/will', encoding='utf-8'))

    A `BoundWalker` is callable. Calling it is an alias for
    `~fs.walk.BoundWalker.walk`.

    """

    def __init__(self, fs, walker_class=Walker):
        self.fs = fs
        self.walker_class = walker_class

    def __repr__(self):
        return "BoundWalker({!r})".format(self.fs)

    def _make_walker(self, *args, **kwargs):
        """Create a walker instance.
        """
        walker = self.walker_class(*args, **kwargs)
        return walker

    def walk(self,
             path='/',
             namespaces=None,
             **kwargs):
        """Walk the directory structure of a filesystem.

        Arguments:
            path (str, optional):
            namespaces (list, optional): A list of namespaces to include
                in the resource information, e.g. ``['basic', 'access']``
                (defaults to ``['basic']``).

        Keyword Arguments:
            ignore_errors (bool): If `True`, any errors reading a
                directory will be ignored, otherwise exceptions will be
                raised.
            on_error (callable): If ``ignore_errors`` is `False`, then
                this callable will be invoked with a path and the exception
                object. It should return `True` to ignore the error, or
                `False` to re-raise it.
            search (str): If ``'breadth'`` then the directory will be
                walked *top down*. Set to ``'depth'`` to walk *bottom up*.
            filter (list): If supplied, this parameter should be a list
                of file name patterns, e.g. ``['*.py']``. Files will only be
                returned if the final component matches one of the
                patterns.
            exclude_dirs (list): A list of patterns that will be used
                to filter out directories from the walk, e.g. ``['*.svn',
                '*.git']``.
            max_depth (int, optional): Maximum directory depth to walk.

        Returns:
            ~collections.Iterator: an iterator of ``(<path>, <dirs>, <files>)``
            named tuples,  where ``<path>`` is an absolute path to a
            directory, and ``<dirs>`` and ``<files>`` are a list of
            `~fs.info.Info` objects for directories and files in ``<path>``.

        Example:
            >>> home_fs = open_fs('~/')
            >>> walker = Walker(filter=['*.py'])
            >>> for path, dirs, files in walker.walk(home_fs, ['details']):
            ...     print("[{}]".format(path))
            ...     print("{} directories".format(len(dirs)))
            ...     total = sum(info.size for info in files)
            ...     print("{} bytes {}".format(total))

        This method invokes `Walker.walk` with bound `FS` object.

        """
        walker = self._make_walker(**kwargs)
        return walker.walk(self.fs, path=path, namespaces=namespaces)

    __call__ = walk

    def files(self, path='/', **kwargs):
        """Walk a filesystem, yielding absolute paths to files.

        Arguments:
            path (str): A path to a directory.

        Keyword Arguments:
            ignore_errors (bool): If `True`, any errors reading a
                directory will be ignored, otherwise exceptions will be
                raised.
            on_error (callable): If ``ignore_errors`` is `False`, then
                this callable will be invoked with a path and the exception
                object. It should return `True` to ignore the error, or
                `False` to re-raise it.
            search (str): If ``'breadth'`` then the directory will be
                walked *top down*. Set to ``'depth'`` to walk *bottom up*.
            filter (list): If supplied, this parameter should be a list
                of file name patterns, e.g. ``['*.py']``. Files will only be
                returned if the final component matches one of the
                patterns.
            exclude_dirs (list): A list of patterns that will be used
                to filter out directories from the walk, e.g. ``['*.svn',
                '*.git']``.
            max_depth (int, optional): Maximum directory depth to walk.

        Returns:
            ~collections.Iterable: An iterable of file paths (absolute
            from the filesystem root).

        This method invokes `Walker.files` with the bound `FS` object.

        """
        walker = self._make_walker(**kwargs)
        return walker.files(self.fs, path=path)

    def dirs(self, path='/', **kwargs):
        """Walk a filesystem, yielding absolute paths to directories.

        Arguments:
            path (str): A path to a directory.

        Keyword Arguments:
            ignore_errors (bool): If `True`, any errors reading a
                directory will be ignored, otherwise exceptions will be
                raised.
            on_error (callable): If ``ignore_errors`` is `False`, then
                this callable will be invoked with a path and the exception
                object. It should return `True` to ignore the error, or
                `False` to re-raise it.
            search (str): If ``'breadth'`` then the directory will be
                walked *top down*. Set to ``'depth'`` to walk *bottom up*.
            exclude_dirs (list): A list of patterns that will be used
                to filter out directories from the walk, e.g. ``['*.svn',
                '*.git']``.
            max_depth (int, optional): Maximum directory depth to walk.

        Returns:
            ~collections.iterable: an iterable of directory paths
            (absolute from the filesystem root).

        This method invokes `Walker.dirs` with the bound `FS` object.

        """
        walker = self._make_walker(**kwargs)
        return walker.dirs(self.fs, path=path)

    def info(self, path='/', namespaces=None, **kwargs):
        """Walk a filesystem, yielding path and `Info` of resources.

        Arguments:
            path (str, optional):
            namespaces (list, optional): A list of namespaces to include
                in the resource information, e.g. ``['basic', 'access']``
                (defaults to ``['basic']``).

        Keyword Arguments:
            ignore_errors (bool): If `True`, any errors reading a
                directory will be ignored, otherwise exceptions will be
                raised.
            on_error (callable): If ``ignore_errors`` is `False`, then
                this callable will be invoked with a path and the exception
                object. It should return `True` to ignore the error, or
                `False` to re-raise it.
            search (str): If ``'breadth'`` then the directory will be
                walked *top down*. Set to ``'depth'`` to walk *bottom up*.
            filter (list): If supplied, this parameter should be a list
                of file name patterns, e.g. ``['*.py']``. Files will only be
                returned if the final component matches one of the
                patterns.
            exclude_dirs (list): A list of patterns that will be used
                to filter out directories from the walk, e.g. ``['*.svn',
                '*.git']``.
            max_depth (int, optional): Maximum directory depth to walk.

        Returns:
            ~collections.Iterable: an iterable yielding tuples of
            ``(<absolute path>, <resource info>)``.

        This method invokes `Walker.info` with the bound `FS` object.

        """
        walker = self._make_walker(**kwargs)
        return walker.info(
            self.fs,
            path=path,
            namespaces=namespaces
        )

# Allow access to default walker from the module
# For example:
#     fs.walk.walk_files()

default_walker = Walker()
walk = default_walker.walk
walk_files = default_walker.files
walk_info = default_walker.info
walk_dirs = default_walker.dirs
