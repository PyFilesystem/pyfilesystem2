from __future__ import unicode_literals

from collections import deque
from functools import partial
import itertools
import weakref

import six

from . import wildcard
from .path import abspath, join, normpath
from .errors import FSError


class Walker(object):
    """
    A walker instance recurses into the directory structure of a
    filesystem.

    """
    # Nothing to do with zombies...

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
            >>> for path in walker.walk_files(wildcards=['*.py']):
            ...     print(path)

        Unless you have written a customized walker class, you will be
        unlikely to need to call this explicitly, as filesystem objects
        already have a bound walker attribute. Here's how you might use
        it::

            >>> from fs import open_fs
            >>> home_fs = open_fs('~/')
            >>> for path in home_fs.walker.walk_files(wildcards=['*.py']):
            ...     print(path)


        :param fs: A filesystem object.
        :returns: a :class:`fs.walk.BoundWalker`

        """
        return BoundWalker(fs, cls())

    def __repr__(self):
        return "Walker()"

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

    def _check_file(self, fs, info, wildcards):
        return (
            wildcard.imatch_any(wildcards, info.name) and
            self.check_file(fs, info)
        )

    def filter_files(self, fs, infos, wildcards):
        """
        Filters a sequence of resource Info objects.

        The default implementation filters those files for which
        :meth:`fs.walk.Walker.check_file` returns True.

        :param fs: A filesystem object.
        :type fs: :class:`fs.base.FS`
        :param infos: A list of :class:`fs.info.Info` instances.
        :type infos: list
        :param wildcards: A list of wildcards.
        :type wildcards: list
        :rtype: list

        """
        _check_file = self._check_file
        return [
            info for info in infos
            if _check_file(fs, info, wildcards)
        ]

    def scan(self, fs, dir_path, on_error, namespaces):
        """
        Get an iterator of :class:`fs.info.Info` objects for a
        directory path.

        :param fs: A filesystem object.
        :type fs: :class:`fs.base.FS`
        :param str dir_path: A path to a directory.
        :param on_error: A callable that takes a path, and an
            :class:`fs.info.Info` instance.

        """
        try:
            return fs.scandir(dir_path, namespaces=namespaces)
        except FSError as error:
            if on_error(dir_path, error):
                return iter(())
            six.reraise(type(error), error)

    def walk(self,
             fs,
             path='/',
             on_error=None,
             search="breadth",
             wildcards=None,
             namespaces=None):
        """
        Walk the directory structure of a filesystem.

        :param fs: A filesystem object.
        :param str path: a path to a directory.
        :param on_error: A callable that accepts an info object, and
            an exception instance. This will be invoked if there is
            an error reading the directory. If the callable returns
            True, the error will be silently ignored, otherwise, it
            will be raised.
        :param str search: One of 'breadth' or 'depth'.
        :param list wildcards: A list of wildcards to filter the files by.
        :param list namespaces: A list of additional namespaces to add to
            the Info objects.
        :returns: Generator of :class:`fs.info.Info` objects.


        Yields tuples of (<absolute dir path>, <dirs>, <files>), where
        ``<dirs>`` and ``<files>`` are a list of :class:`fs.info.Info`
        objects.

        """
        _path = abspath(normpath(path))
        if on_error is None:
            def on_error(info, error):
                return True

        if search == 'breadth':
            do_walk = self._walk_breadth
        elif search == 'depth':
            do_walk = self._walk_depth
        else:
            raise ValueError('unsupported value for search')

        return do_walk(
            fs,
            _path,
            on_error,
            wildcards,
            namespaces or []
        )

    def walk_files(self,
                   fs,
                   path='/',
                   on_error=None,
                   search="breadth",
                   wildcards=None):
        """
        Walk a filesystem, yielding absolute paths to files.

        :param fs: A filesystem object.
        :param str path: A path to a directory.
        :param on_error: A callable that accepts an info object, and
            an exception instance.
        :param str search: One of 'breadth' or 'depth'
        :param list wildcards: A list of wildcards to filter the files by.

        """
        iter_walk = iter(self.walk(
            fs,
            path=path,
            on_error=on_error,
            search=search,
            wildcards=wildcards
        ))
        for _path, _, files in iter_walk:
            for info in files:
                yield join(_path, info.name)

    def walk_dirs(self, fs, path='/', on_error=None, search="breadth"):
        """
        Walk a filesystem, yielding absolute paths to directories.

        :param str fs: A filesystem object.
        :param callable on_error: A callable that accepts an info
            object, and an exception instance.
        :param str search: One of 'breadth' or 'depth'

        """
        iter_walk = self.walk(
            fs,
            path=path,
            search=search,
            on_error=on_error
        )
        for path, dirs, _ in iter_walk:
            for info in dirs:
                yield join(path, info.name)

    def walk_info(self,
                  fs,
                  path='/',
                  on_error=None,
                  search="breadth",
                  wildcards=None,
                  namespaces=None):
        """
        Walk a filesystem, yielding tuples of (<absolute path>,
        <resource info).

        :param str fs: A filesystem object.
        :param str path: A path to a directory.
        :param on_error: A callable that accepts an info object, and
            an exception instance.
        :param str search: One of 'breadth' or 'depth'
        :param list namespaces: A list of additional namespaces to add to
            the Info objects.

        """
        iter_walk = iter(self.walk(
            fs,
            path=path,
            on_error=on_error,
            search=search,
            wildcards=wildcards,
            namespaces=namespaces,
        ))
        for _path, dirs, files in iter_walk:
            for info in itertools.chain(dirs, files):
                yield join(_path, info.name), info

    def _walk_breadth(self, fs, path, on_error, wildcards, namespaces):
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
            for info in self.scan(fs, dir_path, on_error, namespaces):
                if info.is_dir:
                    dirs.append(info)
                    if self.check_open_dir(fs, info):
                        push(join(dir_path, info.name))
                else:
                    files.append(info)
            yield (
                dir_path,
                dirs,
                self.filter_files(fs, files, wildcards)
            )

    def _walk_depth(self, fs, path, on_error, wildcards, namespaces):
        """
        Walk files using a depth first search.

        """
        # No recursion!

        def scan(scan_path):
            return self.scan(fs, scan_path, on_error, namespaces)

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
                    self.filter_files(fs, files, wildcards)
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

    def __init__(self, fs, walker):
        self._fs = weakref.ref(fs)
        self.walker = walker
        self.walk = partial(walker.walk, fs)
        self.walk_files = partial(walker.walk_files, fs)
        self.walk_dirs = partial(walker.walk_dirs, fs)
        self.walk_info = partial(walker.walk_info, fs)

    def __repr__(self):
        return "BoundWalker({!r}, {!r})".format(self.fs, self.walker)

    @property
    def fs(self):
        """Gets the weakref FS object."""
        return self._fs()


walker = Walker()
walk = walker.walk
walk_files = walker.walk_files
walk_dirs = walker.walk_dirs
walk_info = walker.walk_info
