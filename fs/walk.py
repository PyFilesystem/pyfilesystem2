from __future__ import unicode_literals

from collections import deque

import itertools
import weakref

import six

from . import wildcard
from .path import abspath, join, normpath
from .errors import FSError
from ._repr import make_repr



class WalkerBase(object):
    """Base class for a Walker."""

    # Nothing to do with zombies...

    def __init__(self):
        super(WalkerBase, self).__init__()

    def check_open_dir(self, fs, info):
        """
        Check if a directory should be opened. Override to exclude
        directories from the walk.

        :param fs: A filesystem object.
        :type fs: :class:`fs.base.FS`
        :param info: A :class:`fs.info.Info` object.
        :rtype: bool

        """
        return True

    def check_file(self, fs, info):
        """
        Check if a filename should be included in the walk. Override to
        exclude files from the walk.

        :param fs: A filesystem object.
        :type fs: :class:`fs.base.FS`
        :param info: A :class:`fs.info.Info` object.
        :rtype: bool

        """
        return True

    def filter_files(self, fs, infos):
        """
        Filters a sequence of resource Info objects.

        The default implementation filters those files for which
        :meth:`fs.walk.Walker.check_file` returns True.

        :param fs: A filesystem object.
        :type fs: :class:`fs.base.FS`
        :param infos: A list of :class:`fs.info.Info` instances.
        :type infos: list
        :rtype: list

        """
        _check_file = self.check_file
        return [
            info for info in infos
            if _check_file(fs, info)
        ]

    def walk(self, fs, path='/', namespaces=None):
        """
        Walk the directory structure of a filesystem.

        The return value is an iterable of (<absolute dir path>, <dirs>,
        <files>) tuples,  where ``<dirs>`` and ``<files>`` are a list of
        :class:`fs.info.Info` objects.

        :param fs: A filesystem object.
        :param str path: a path to a directory.
        :returns: Iterator of tuples.

        """
        raise NotImplementedError

    def walk_files(self, fs, path='/'):
        """
        Walk a filesystem, yielding absolute paths to files.

        :param fs: A filesystem object.
        :param str path: A path to a directory.
        :returns: An iterable of file paths.

        """
        iter_walk = iter(self.walk(fs, path=path))
        for _path, _, files in iter_walk:
            for info in files:
                yield join(_path, info.name)

    def walk_dirs(self, fs, path='/'):
        """
        Walk a filesystem, yielding absolute paths to directories.

        :param str fs: A filesystem object.
        :param str path: A path to a directory.

        """
        for path, dirs, _ in self.walk(fs, path=path):
            for info in dirs:
                yield join(path, info.name)

    def walk_info(self, fs, path='/', namespaces=None):
        """
        Walk a filesystem, yielding tuples of (<absolute path>,
        <resource info).

        :param str fs: A filesystem object.
        :param str path: A path to a directory.
        :param list namespaces: A list of additional namespaces to add to
            the Info objects.
        :returns: An iterable of :class:`fs.info.Info` objects.

        """
        _walk = self.walk(fs, path=path, namespaces=namespaces)
        for _path, dirs, files in _walk:
            for info in itertools.chain(dirs, files):
                yield join(_path, info.name), info

class Walker(WalkerBase):
    """
    Standard FS walker. Fully featured enough for most purposes.

    """

    def __init__(self,
                 ignore_errors=False,
                 on_error=None,
                 search="breadth",
                 wildcards=None,
                 exclude_dirs=None):
        if search not in ('breadth', 'depth'):
            raise ValueError("search must be 'breadth' or 'depth'")
        self.ignore_errors = ignore_errors
        if ignore_errors:
            if on_error is None:
                raise ValueError(
                    'on_error is invalid when ignore_errors==True')
            on_error = lambda path, error: True
        self.on_error = on_error or (lambda path, error: True)
        self.search = search
        self.wildcards = wildcards
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
            >>> for path in walker.files(wildcards=['*.py']):
            ...     print(path)

        Unless you have written a customized walker class, you will be
        unlikely to need to call this explicitly, as filesystem objects
        already have a ``walk`` attribute which is a bound walker
        object. Here's how you might use it::

            >>> from fs import open_fs
            >>> home_fs = open_fs('~/')
            >>> for path in home_fs.walk.files(wildcards=['*.py']):
            ...     print(path)

        :param fs: A filesystem object.
        :returns: a :class:`fs.walk.BoundWalker`

        """
        return BoundWalker(fs)

    def __repr__(self):
        return make_repr([
            ('ignore_errors', self.ignore_errors, False),
            ('on_error', self.on_error, None),
            ('search', self.search, 'breadth'),
            ('wildcards', self.wildcards, None),
            ('exclude_dirs', self.exclude_dirs, None)
        ])


    def check_open_dir(self, fs, info):
        if self.exclude_dirs is None:
            return True
        return not fs.match(self.exclude_dirs, info.name)

    def check_file(self, fs, info):
        return fs.match(self.wildcards, info.name)

    def _scan(self, fs, dir_path, namespaces):
        """
        Get an iterator of :class:`fs.info.Info` objects for a
        directory path.

        :param fs: A filesystem object.
        :type fs: :class:`fs.base.FS`
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

        The return value is an iterable of (<absolute dir path>, <dirs>,
        <files>) tuples,  where ``<dirs>`` and ``<files>`` are a list of
        :class:`fs.info.Info` objects.

        :param fs: A filesystem object.
        :param str path: a path to a directory.
        :param list namespaces: A list of additional namespaces to add to
            the Info objects.
        :returns: Iterator of tuples.

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
                    dirs.append(info)
                    if self.check_open_dir(fs, info):
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
                    dirs.append(info)
                    if self.check_open_dir(fs, info):
                        _path = join(dir_path, info.name)
                        push((
                            _path, scan(_path), [], []
                        ))
                else:
                    files.append(info)


class BoundWalker(object):
    """A Walker that works with a single FS object."""

    def __init__(self, fs, walker_class=Walker):
        self._fs = weakref.ref(fs)
        self.walker_class = walker_class

    def __repr__(self):
        return "BoundWalker({!r})".format(self.fs)

    @property
    def fs(self):
        return self._fs()

    def _make_walker(self, *args, **kwargs):
        """Create a walker instance."""
        walker = self.walker_class(*args, **kwargs)
        return walker

    def __call__(self,
                 path='/',
                 ignore_errors=False,
                 on_error=None,
                 search="breadth",
                 wildcards=None,
                 namespaces=None,
                 exclude_dirs=None):
        """Invokes :meth:`fs.walk.Walker.walk` with bound FS object."""
        walker = self._make_walker(
            ignore_errors=ignore_errors,
            on_error=on_error,
            search=search,
            wildcards=wildcards,
            exclude_dirs=exclude_dirs
        )
        return walker.walk(self.fs, path=path, namespaces=namespaces)

    def files(self,
              path='/',
              ignore_errors=False,
              on_error=None,
              search="breadth",
              wildcards=None,
              exclude_dirs=None):
        """
        Invokes :meth:`fs.walk.Walker.walk_files` with bound FS object.

        """
        walker = self._make_walker(
            ignore_errors=ignore_errors,
            on_error=on_error,
            search=search,
            wildcards=wildcards,
            exclude_dirs=exclude_dirs
        )
        return walker.walk_files(self.fs, path=path)

    def dirs(self,
             path='/',
             ignore_errors=False,
             on_error=None,
             search="breadth",
             exclude_dirs=None):
        """
        Invokes :meth:`fs.walk.Walker.walk_dirs` with bound FS object.

        """
        walker = self._make_walker(
            ignore_errors=ignore_errors,
            on_error=on_error,
            search=search,
            exclude_dirs=exclude_dirs
        )
        return walker.walk_dirs(self.fs, path=path)

    def info(self,
             path='/',
             on_error=None,
             search="breadth",
             wildcards=None,
             exclude_dirs=None,
             namespaces=None):
        """
        Invokes :meth:`fs.walk.Walker.walk_indo` with bound FS object.

        """
        walker = self._make_walker(
           on_error=on_error,
           search=search,
           wildcards=wildcards,
           exclude_dirs=exclude_dirs
        )
        return walker.walk_info(self.fs, path=path, namespaces=namespaces)

# Allow access to default walker from the module
# For example:
#     fs.walk.walk_files()

default_walker = Walker()
walk = default_walker.walk
walk_files = default_walker.walk_files
walk_info = default_walker.walk_info
walk_dirs = default_walker.walk_dirs
