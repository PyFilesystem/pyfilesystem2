"""Useful functions for working with glob patterns.
"""

from __future__ import unicode_literals

import typing

import re
from collections import namedtuple

from . import wildcard
from ._repr import make_repr
from .lrucache import LRUCache
from .path import iteratepath

GlobMatch = namedtuple("GlobMatch", ["path", "info"])
Counts = namedtuple("Counts", ["files", "directories", "data"])
LineCounts = namedtuple("LineCounts", ["lines", "non_blank"])

if typing.TYPE_CHECKING:
    from typing import Iterator, List, Optional, Pattern, Text, Tuple

    from .base import FS


_PATTERN_CACHE = LRUCache(
    1000
)  # type: LRUCache[Tuple[Text, bool], Tuple[int, bool, Pattern]]


def _translate_glob(pattern, case_sensitive=True):
    levels = 0
    recursive = False
    re_patterns = [""]
    for component in iteratepath(pattern):
        if component == "**":
            re_patterns.append(".*/?")
            recursive = True
        else:
            re_patterns.append(
                "/" + wildcard._translate(component, case_sensitive=case_sensitive)
            )
        levels += 1
    re_glob = "(?ms)^" + "".join(re_patterns) + ("/$" if pattern.endswith("/") else "$")
    return (
        levels,
        recursive,
        re.compile(re_glob, 0 if case_sensitive else re.IGNORECASE),
    )


def match(pattern, path):
    # type: (str, str) -> bool
    """Compare a glob pattern with a path (case sensitive).

    Arguments:
        pattern (str): A glob pattern.
        path (str): A path.

    Returns:
        bool: ``True`` if the path matches the pattern.

    Example:

        >>> from fs.glob import match
        >>> match("**/*.py", "/fs/glob.py")
        True

    """
    try:
        levels, recursive, re_pattern = _PATTERN_CACHE[(pattern, True)]
    except KeyError:
        levels, recursive, re_pattern = _translate_glob(pattern, case_sensitive=True)
        _PATTERN_CACHE[(pattern, True)] = (levels, recursive, re_pattern)
    return bool(re_pattern.match(path))


def imatch(pattern, path):
    # type: (str, str) -> bool
    """Compare a glob pattern with a path (case insensitive).

    Arguments:
        pattern (str): A glob pattern.
        path (str): A path.

    Returns:
        bool: ``True`` if the path matches the pattern.

    """
    try:
        levels, recursive, re_pattern = _PATTERN_CACHE[(pattern, False)]
    except KeyError:
        levels, recursive, re_pattern = _translate_glob(pattern, case_sensitive=True)
        _PATTERN_CACHE[(pattern, False)] = (levels, recursive, re_pattern)
    return bool(re_pattern.match(path))


class Globber(object):
    """A generator of glob results."""

    def __init__(
        self,
        fs,
        pattern,
        path="/",
        namespaces=None,
        case_sensitive=True,
        exclude_dirs=None,
    ):
        # type: (FS, str, str, Optional[List[str]], bool, Optional[List[str]]) -> None
        """Create a new Globber instance.

        Arguments:
            fs (~fs.base.FS): A filesystem object
            pattern (str): A glob pattern, e.g. ``"**/*.py"``
            path (str): A path to a directory in the filesystem.
            namespaces (list): A list of additional info namespaces.
            case_sensitive (bool): If ``True``, the path matching will be
                case *sensitive* i.e. ``"FOO.py"`` and ``"foo.py"`` will be
                different, otherwise path matching will be case *insensitive*.
            exclude_dirs (list): A list of patterns to exclude when searching,
                e.g. ``["*.git"]``.

        """
        self.fs = fs
        self.pattern = pattern
        self.path = path
        self.namespaces = namespaces
        self.case_sensitive = case_sensitive
        self.exclude_dirs = exclude_dirs

    def __repr__(self):
        return make_repr(
            self.__class__.__name__,
            self.fs,
            self.pattern,
            path=(self.path, "/"),
            namespaces=(self.namespaces, None),
            case_sensitive=(self.case_sensitive, True),
            exclude_dirs=(self.exclude_dirs, None),
        )

    def _make_iter(self, search="breadth", namespaces=None):
        # type: (str, List[str]) -> Iterator[GlobMatch]
        try:
            levels, recursive, re_pattern = _PATTERN_CACHE[
                (self.pattern, self.case_sensitive)
            ]
        except KeyError:
            levels, recursive, re_pattern = _translate_glob(
                self.pattern, case_sensitive=self.case_sensitive
            )

        for path, info in self.fs.walk.info(
            path=self.path,
            namespaces=namespaces or self.namespaces,
            max_depth=None if recursive else levels,
            search=search,
            exclude_dirs=self.exclude_dirs,
        ):
            if info.is_dir:
                path += "/"
            if re_pattern.match(path):
                yield GlobMatch(path, info)

    def __iter__(self):
        # type: () -> Iterator[GlobMatch]
        """Get an iterator of :class:`fs.glob.GlobMatch` objects."""
        return self._make_iter()

    def count(self):
        # type: () -> Counts
        """Count files / directories / data in matched paths.

        Example:
            >>> my_fs.glob('**/*.py').count()
            Counts(files=2, directories=0, data=55)

        Returns:
            `~Counts`: A named tuple containing results.

        """
        directories = 0
        files = 0
        data = 0
        for _path, info in self._make_iter(namespaces=["details"]):
            if info.is_dir:
                directories += 1
            else:
                files += 1
            data += info.size
        return Counts(directories=directories, files=files, data=data)

    def count_lines(self):
        # type: () -> LineCounts
        """Count the lines in the matched files.

        Returns:
            `~LineCounts`: A named tuple containing line counts.

        Example:
            >>> my_fs.glob('**/*.py').count_lines()
            LineCounts(lines=4, non_blank=3)

        """
        lines = 0
        non_blank = 0
        for path, info in self._make_iter():
            if info.is_file:
                for line in self.fs.open(path, "rb"):
                    lines += 1
                    if line.rstrip():
                        non_blank += 1
        return LineCounts(lines=lines, non_blank=non_blank)

    def remove(self):
        # type: () -> int
        """Remove all matched paths.

        Returns:
            int: Number of file and directories removed.

        Example:
            >>> my_fs.glob('**/*.pyc').remove()
            2

        """
        removes = 0
        for path, info in self._make_iter(search="depth"):
            if info.is_dir:
                self.fs.removetree(path)
            else:
                self.fs.remove(path)
            removes += 1
        return removes


class BoundGlobber(object):
    """A `~fs.glob.Globber` object bound to a filesystem.

    An instance of this object is available on every Filesystem object
    as the `~fs.base.FS.glob` property.

    """

    __slots__ = ["fs"]

    def __init__(self, fs):
        # type: (FS) -> None
        """Create a new bound Globber.

        Arguments:
            fs (FS): A filesystem object to bind to.

        """
        self.fs = fs

    def __repr__(self):
        return make_repr(self.__class__.__name__, self.fs)

    def __call__(
        self, pattern, path="/", namespaces=None, case_sensitive=True, exclude_dirs=None
    ):
        # type: (str, str, Optional[List[str]], bool, Optional[List[str]]) -> Globber
        """Match resources on the bound filesystem againsts a glob pattern.

        Arguments:
            pattern (str): A glob pattern, e.g. ``"**/*.py"``
            namespaces (list): A list of additional info namespaces.
            case_sensitive (bool): If ``True``, the path matching will be
                case *sensitive* i.e. ``"FOO.py"`` and ``"foo.py"`` will
                be different, otherwise path matching will be case **insensitive**.
            exclude_dirs (list): A list of patterns to exclude when searching,
                e.g. ``["*.git"]``.

        Returns:
            `Globber`: An object that may be queried for the glob matches.

        """
        return Globber(
            self.fs,
            pattern,
            path,
            namespaces=namespaces,
            case_sensitive=case_sensitive,
            exclude_dirs=exclude_dirs,
        )
