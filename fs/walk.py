"""

The machinery for walking a filesystem. See :ref:`walking` for details.

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


"""A 'step' in a directory walk."""
Step = namedtuple('Step', 'path, dirs, files')


class WalkerBase(object):
    """
    The base class for a Walker.

    To create a custom walker, implement
    :meth:`~fs.walk.WalkerBase.walk` in a sub-class.

    See :meth:`~fs.walk.Walker` for a fully featured walker object that
    should be adequate for all but your most exotic directory walking
    needs.

    """

    def walk(self, fs, path='/', namespaces=None):
        """
        Walk the directory structure of a filesystem.

        :param fs: A FS object.
        :param str path: a path to a directory.
        :param list namespaces: A list of additional namespaces to add
            to the Info objects.
        :returns: Iterator of :class:`~fs.walk.Step` named tuples.

        """
        raise NotImplementedError

    def files(self, fs, path='/'):
        """
        Walk a filesystem, yielding absolute paths to files.

        :param fs: A FS object.
        :param str path: A path to a directory.
        :returns: An iterable of file paths.

        """
        iter_walk = iter(self.walk(fs, path=path))
        for _path, _, files in iter_walk:
            for info in files:
                yield join(_path, info.name)

    def dirs(self, fs, path='/'):
        """
        Walk a filesystem, yielding absolute paths to directories.

        :param str fs: A FS object.
        :param str path: A path to a directory.

        """
        for path, dirs, _ in self.walk(fs, path=path):
            for info in dirs:
                yield join(path, info.name)

    def info(self, fs, path='/', namespaces=None):
        """
        Walk a filesystem, yielding tuples of ``(<absolute path>,
        <resource info>)``.

        :param str fs: A FS object.
        :param str path: A path to a directory.
        :param list namespaces: A list of additional namespaces to add
            to the Info objects.
        :returns: An iterable of :class:`~fs.info.Info` objects.

        """
        _walk = self.walk(fs, path=path, namespaces=namespaces)
        for _path, dirs, files in _walk:
            for info in itertools.chain(dirs, files):
                yield join(_path, info.name), info


class Walker(WalkerBase):
    """
    A walker object recursively lists directories in a filesystem.

    :param bool ignore_errors: If true, any errors reading a
        directory will be ignored, otherwise exceptions will be
        raised.
    :param callable on_error: If ``ignore_errors`` is false, then
        this callable will be invoked with a path and the exception
        object. It should return True to ignore the error, or False
        to re-raise it.
    :param str search: If ``'breadth'`` then the directory will be
        walked *top down*. Set to ``'depth'`` to walk *bottom up*.
    :param list filter: If supplied, this parameter should be a list of
        filename patterns, e.g. ``['*.py']``. Files will only be
        returned if the final component matches one of the patterns.
    :param list exclude_dirs: A list of patterns that will be used
        to filter out directories from the walk. e.g. ``['*.svn',
        '*.git']``.

    """

    def __init__(self,
                 ignore_errors=False,
                 on_error=None,
                 search="breadth",
                 filter=None,
                 exclude_dirs=None):
        if search not in ('breadth', 'depth'):
            raise ValueError("search must be 'breadth' or 'depth'")
        self.ignore_errors = ignore_errors
        if ignore_errors:
            assert on_error is None,\
                'on_error is invalid when ignore_errors==True'
            on_error = lambda path, error: True
        self.on_error = on_error or (lambda path, error: True)
        self.search = search
        self.filter = filter
        self.exclude_dirs = exclude_dirs
        super(Walker, self).__init__()

    @classmethod
    def bind(cls, fs):
        """
        This *binds* in instance of the Walker to a given filesystem, so
        that you won't need to explicitly provide the filesystem as a
        parameter. Here's an example of binding::

            >>> from fs import open_fs
            >>> from fs.walk import Walker
            >>> home_fs = open_fs('~/')
            >>> walker = Walker.bind(home_fs)
            >>> for path in walker.files(filter=['*.py']):
            ...     print(path)

        Unless you have written a customized walker class, you will be
        unlikely to need to call this explicitly, as filesystem objects
        already have a ``walk`` attribute which is a bound walker
        object. Here's how you might use it::

            >>> from fs import open_fs
            >>> home_fs = open_fs('~/')
            >>> for path in home_fs.walk.files(filter=['*.py']):
            ...     print(path)

        :param fs: A filesystem object.
        :returns: a :class:`~fs.walk.BoundWalker`

        """
        return BoundWalker(fs)

    def __repr__(self):
        return make_repr(
            self.__class__.__name__,
            ignore_errors=(self.ignore_errors, False),
            on_error=(self.on_error, None),
            search=(self.search, 'breadth'),
            filter=(self.filter, None),
            exclude_dirs=(self.exclude_dirs, None)
        )

    def filter_files(self, fs, infos):
        """
        Filters a sequence of resource Info objects.

        The default implementation filters those files for which
        :meth:`~fs.walk.Walker.check_file` returns True.

        :param fs: A FS object.
        :type fs: :class:`~fs.base.FS`
        :param infos: A list of :class:`~fs.info.Info` instances.
        :type infos: list
        :rtype: list

        """
        _check_file = self.check_file
        return [
            info for info in infos
            if _check_file(fs, info)
        ]


    def check_open_dir(self, fs, info):
        """
        Check if a directory should be opened. Override to exclude
        directories from the walk.

        :param fs: A FS object.
        :type fs: :class:`~fs.base.FS`
        :param info: A :class:`~fs.info.Info` object.
        :rtype: bool

        """
        if self.exclude_dirs is None:
            return True
        return not fs.match(self.exclude_dirs, info.name)

    def check_file(self, fs, info):
        """
        Check if a filename should be included in the walk. Override to
        exclude files from the walk.

        :param fs: A FS object.
        :type fs: :class:`~fs.base.FS`
        :param info: A :class:`~fs.info.Info` object.
        :rtype: bool

        """
        return fs.match(self.filter, info.name)

    def _scan(self, fs, dir_path, namespaces):
        """
        Get an iterator of :class:`~fs.info.Info` objects for a
        directory path.

        :param fs: A FS object.
        :type fs: :class:`~fs.base.FS`
        :param str dir_path: A path to a directory.

        """
        try:
            return fs.scandir(dir_path, namespaces=namespaces)
        except FSError as error:
            if self.on_error(dir_path, error):
                return iter(())
            six.reraise(type(error), error)

    def walk(self, fs, path='/', namespaces=None):
        """
        Walk the directory structure of a filesystem.

        :param fs: A FS object.
        :param str path: a path to a directory.
        :param list namespaces: A list of additional namespaces to add
            to the Info objects.
        :returns: :class:`~fs.walk.Step` iterator.

        The return value is an iterator of ``(<path>, <dirs>, <files>)``
        named tuples,  where ``<path>`` is an absolute path to a
        directory, and ``<dirs>`` and ``<files>`` are a list of
        :class:`~fs.info.Info` objects for directories and files
        in ``<path>``.

        Here's an example::

            home_fs = open_fs('~/')
            walker = Walker(filter=['*.py'])
            for path, dirs, files in walker.walk(home_fs, namespaces=['details']):
                print("[{}]".format(path))
                print("{} directories".format(len(dirs)))
                total = sum(info.size for info in files)
                print("{} bytes {}".format(total))

        """
        _path = abspath(normpath(path))

        if self.search == 'breadth':
            do_walk = self._walk_breadth
        elif self.search == 'depth':
            do_walk = self._walk_depth

        return do_walk(fs, _path, namespaces=namespaces)

    def _walk_breadth(self, fs, path, namespaces=None):
        """
        Walk files using a breadth first search.

        """
        queue = deque([path])
        push = queue.appendleft
        pop = queue.pop

        while queue:
            dir_path = pop()
            dirs = []
            files = []
            for info in self._scan(fs, dir_path, namespaces=namespaces):
                if info.is_dir:
                    if self.check_open_dir(fs, info):
                        dirs.append(info)
                        push(join(dir_path, info.name))
                else:
                    files.append(info)
            yield (
                dir_path,
                dirs,
                self.filter_files(fs, files)
            )

    def _walk_depth(self, fs, path, namespaces=None):
        """
        Walk files using a depth first search.

        """
        # No recursion!

        def scan(path):
            return self._scan(fs, path, namespaces=namespaces)

        stack = [(
            path, scan(path), [], []
        )]
        push = stack.append

        while stack:
            dir_path, iter_files, dirs, files = stack[-1]
            try:
                info = next(iter_files)
            except StopIteration:
                yield (
                    dir_path,
                    dirs,
                    self.filter_files(fs, files)
                )
                del stack[-1]
            else:
                if info.is_dir:
                    if self.check_open_dir(fs, info):
                        dirs.append(info)
                        _path = join(dir_path, info.name)
                        push((
                            _path, scan(_path), [], []
                        ))
                else:
                    files.append(info)


class BoundWalker(object):
    """
    A class that binds a :class:`~fs.walk.Walker` instance to a FS
    object.

    :param fs: A FS object.
    :param walker_class: A :class:`~fs.walk.WalkerBase` sub-class. The
        default uses :class:`~fs.walk.Walker`.

    You will typically not need to create instances of this class
    explicitly. Filesystems have a ``walk`` property which returns a
    ``BoundWalker`` object.

        >>> import fs
        >>> home_fs = fs.open_fs('~/')
        >>> home_fs.walk
        BoundWalker(OSFS('/Users/will', encoding='utf-8'))

    A BoundWalker is callable. Calling it is an alias for
    :meth:`~fs.walk.BoundWalker.walk`.

    """

    def __init__(self, fs, walker_class=Walker):
        self.fs = fs
        self.walker_class = walker_class

    def __repr__(self):
        return "BoundWalker({!r})".format(self.fs)

    def _make_walker(self, *args, **kwargs):
        """Create a walker instance."""
        walker = self.walker_class(*args, **kwargs)
        return walker

    def walk(self,
             path='/',
             namespaces=None,
             **kwargs):
        """
        Walk the directory structure of a filesystem.

        :param str path: A path to a directory.
        :param bool ignore_errors: If true, any errors reading a
            directory will be ignored, otherwise exceptions will be
            raised.
        :param callable on_error: If ``ignore_errors`` is false, then
            this callable will be invoked with a path and the exception
            object. It should return True to ignore the error, or False
            to re-raise it.
        :param str search: If ``'breadth'`` then the directory will be
            walked *top down*. Set to ``'depth'`` to walk *bottom up*.
        :param list filter: If supplied, this parameter should be a list
            of file name patterns, e.g. ``['*.py']``. Files will only be
            returned if the final component matches one of the
            patterns.
        :param list exclude_dirs: A list of patterns that will be used
            to filter out directories from the walk, e.g. ``['*.svn',
            '*.git']``.
        :returns: :class:`~fs.walk.Step` iterator.

        The return value is an iterator of ``(<path>, <dirs>, <files>)``
        named tuples,  where ``<path>`` is an absolute path to a
        directory, and ``<dirs>`` and ``<files>`` are a list of
        :class:`~fs.info.Info` objects for directories and files
        in ``<path>``.

        Here's an example::

            home_fs = open_fs('~/')
            walker = Walker(filter=['*.py'])
            for path, dirs, files in walker.walk(home_fs, namespaces=['details']):
                print("[{}]".format(path))
                print("{} directories".format(len(dirs)))
                total = sum(info.size for info in files)
                print("{} bytes {}".format(total))

        This method invokes :meth:`~fs.walk.Walker.walk` with bound FS
        object.

        """
        walker = self._make_walker(**kwargs)
        return walker.walk(self.fs, path=path, namespaces=namespaces)

    __call__ = walk

    def files(self, path='/', **kwargs):
        """
        Walk a filesystem, yielding absolute paths to files.

        :param str path: A path to a directory.
        :param bool ignore_errors: If true, any errors reading a
            directory will be ignored, otherwise exceptions will be
            raised.
        :param callable on_error: If ``ignore_errors`` is false, then
            this callable will be invoked with a path and the exception
            object. It should return True to ignore the error, or False
            to re-raise it.
        :param str search: If ``'breadth'`` then the directory will be
            walked *top down*. Set to ``'depth'`` to walk *bottom up*.
        :param list filter: If supplied, this parameter should be a list
            of file name patterns, e.g. ``['*.py']``. Files will only be
            returned if the final component matches one of the
            patterns.
        :param list exclude_dirs: A list of patterns that will be used
            to filter out directories from the walk, e.g. ``['*.svn',
            '*.git']``.
        :returns: An iterable of file paths (absolute from the
            filesystem root).

        This method invokes :meth:`~fs.walk.Walker.files` with the bound
        FS object.

        """
        walker = self._make_walker(**kwargs)
        return walker.files(self.fs, path=path)

    def dirs(self, path='/', **kwargs):
        """
        Walk a filesystem, yielding absolute paths to directories.

        :param str path: A path to a directory.
        :param bool ignore_errors: If true, any errors reading a
            directory will be ignored, otherwise exceptions will be
            raised.
        :param callable on_error: If ``ignore_errors`` is false, then
            this callable will be invoked with a path and the exception
            object. It should return True to ignore the error, or False
            to re-raise it.
        :param str search: If ``'breadth'`` then the directory will be
            walked *top down*. Set to ``'depth'`` to walk *bottom up*.
        :param list exclude_dirs: A list of patterns that will be used
            to filter out directories from the walk, e.g. ``['*.svn',
            '*.git']``.
        :returns: An iterable of directory paths (absolute from the FS
            root).

        This method invokes :meth:`~fs.walk.Walker.dirs` with the bound
        FS object.

        """
        walker = self._make_walker(**kwargs)
        return walker.dirs(self.fs, path=path)

    def info(self, path='/', namespaces=None, **kwargs):
        """
        Walk a filesystem, yielding tuples of ``(<absolute path>,
        <resource info>)``.

        :param str path: A path to a directory.
        :param bool ignore_errors: If true, any errors reading a
            directory will be ignored, otherwise exceptions will be
            raised.
        :param callable on_error: If ``ignore_errors`` is false, then
            this callable will be invoked with a path and the exception
            object. It should return True to ignore the error, or False
            to re-raise it.
        :param str search: If ``'breadth'`` then the directory will be
            walked *top down*. Set to ``'depth'`` to walk *bottom up*.
        :param list filter: If supplied, this parameter should be a list
            of file name patterns, e.g. ``['*.py']``. Files will only be
            returned if the final component matches one of the
            patterns.
        :param list exclude_dirs: A list of patterns that will be used
            to filter out directories from the walk, e.g. ``['*.svn',
            '*.git']``.
        :returns: An iterable :class:`~fs.info.Info` objects.

        This method invokes :meth:`~fs.walk.Walker.info` with the bound
        FS object.

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
