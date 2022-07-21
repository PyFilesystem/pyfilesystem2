"""Useful functions for working with glob patterns.
"""

from __future__ import unicode_literals

import typing
from functools import partial

import re
from collections import namedtuple

from ._repr import make_repr
from .lrucache import LRUCache
from .path import iteratepath


GlobMatch = namedtuple("GlobMatch", ["path", "info"])
Counts = namedtuple("Counts", ["files", "directories", "data"])
LineCounts = namedtuple("LineCounts", ["lines", "non_blank"])

if typing.TYPE_CHECKING:
    from typing import (
        Iterator,
        List,
        Optional,
        Pattern,
        Text,
        Tuple,
        Iterable,
        Callable,
    )
    from .base import FS


_PATTERN_CACHE = LRUCache(
    1000
)  # type: LRUCache[Tuple[Text, bool], Tuple[Optional[int], Pattern]]


def _split_pattern_by_sep(pattern):
    # type: (Text) -> List[Text]
    """Split a glob pattern at its directory seperators (/).

    Takes into account escaped cases like [/].
    """
    indices = [-1]
    bracket_open = False
    for i, c in enumerate(pattern):
        if c == "/" and not bracket_open:
            indices.append(i)
        elif c == "[":
            bracket_open = True
        elif c == "]":
            bracket_open = False

    indices.append(len(pattern))
    return [pattern[i + 1 : j] for i, j in zip(indices[:-1], indices[1:])]


def _translate(pattern):
    # type: (Text) -> Text
    """Translate a glob pattern without '**' to a regular expression.

    There is no way to quote meta-characters.

    Arguments:
        pattern (str): A glob pattern.

    Returns:
        str: A regex equivalent to the given pattern.

    """
    i, n = 0, len(pattern)
    res = []
    while i < n:
        c = pattern[i]
        i = i + 1
        if c == "*":
            if i < n and pattern[i] == "*":
                raise ValueError("glob._translate does not support '**' patterns.")
            res.append("[^/]*")
        elif c == "?":
            res.append("[^/]")
        elif c == "[":
            j = i
            if j < n and pattern[j] == "!":
                j = j + 1
            if j < n and pattern[j] == "]":
                j = j + 1
            while j < n and pattern[j] != "]":
                j = j + 1
            if j >= n:
                res.append("\\[")
            else:
                stuff = pattern[i:j].replace("\\", "\\\\")
                i = j + 1
                if stuff[0] == "!":
                    stuff = "^/" + stuff[1:]
                elif stuff[0] == "^":
                    stuff = "\\" + stuff
                res.append("[%s]" % stuff)
        else:
            res.append(re.escape(c))
    return "".join(res)


def _translate_glob(pattern):
    # type: (Text) -> Tuple[Optional[int], Text]
    """Translate a glob pattern to a regular expression.

    There is no way to quote meta-characters.

    Arguments:
        pattern (str): A glob pattern.

    Returns:
        Tuple[Optional[int], Text]: The first component describes the levels
            of depth this glob pattern goes to; basically the number of "/" in
            the pattern. If there is a "**" in the glob pattern, the depth is
            basically unbounded, and this component is `None` instead.
            The second component is the regular expression.

    """
    recursive = False
    re_patterns = [""]
    for component in iteratepath(pattern):
        if "**" in component:
            recursive = True
            split = component.split("**")
            split_re = [_translate(s) for s in split]
            re_patterns.append("/?" + ".*/?".join(split_re))
        else:
            re_patterns.append("/" + _translate(component))
    re_glob = "(?ms)^" + "".join(re_patterns) + ("/$" if pattern.endswith("/") else "$")
    return pattern.count("/") + 1 if not recursive else None, re_glob


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
        levels, re_pattern = _PATTERN_CACHE[(pattern, True)]
    except KeyError:
        levels, re_str = _translate_glob(pattern)
        re_pattern = re.compile(re_str)
        _PATTERN_CACHE[(pattern, True)] = (levels, re_pattern)
    if path and path[0] != "/":
        path = "/" + path
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
        levels, re_pattern = _PATTERN_CACHE[(pattern, False)]
    except KeyError:
        levels, re_str = _translate_glob(pattern)
        re_pattern = re.compile(re_str, re.IGNORECASE)
        _PATTERN_CACHE[(pattern, False)] = (levels, re_pattern)
    if path and path[0] != "/":
        path = "/" + path
    return bool(re_pattern.match(path))


def match_any(patterns, path):
    # type: (Iterable[Text], Text) -> bool
    """Test if a path matches any of a list of patterns.

    Will return `True` if ``patterns`` is an empty list.

    Arguments:
        patterns (list): A list of wildcard pattern, e.g ``["*.py",
            "*.pyc"]``
        path (str): A resource path.

    Returns:
        bool: `True` if the path matches at least one of the patterns.

    """
    if not patterns:
        return True
    return any(match(pattern, path) for pattern in patterns)


def imatch_any(patterns, path):
    # type: (Iterable[Text], Text) -> bool
    """Test if a path matches any of a list of patterns (case insensitive).

    Will return `True` if ``patterns`` is an empty list.

    Arguments:
        patterns (list): A list of wildcard pattern, e.g ``["*.py",
            "*.pyc"]``
        path (str): A resource path.

    Returns:
        bool: `True` if the path matches at least one of the patterns.

    """
    if not patterns:
        return True
    return any(imatch(pattern, path) for pattern in patterns)


def get_matcher(patterns, case_sensitive, accept_prefix=False):
    # type: (Iterable[Text], bool, bool) -> Callable[[Text], bool]
    """Get a callable that matches paths against the given patterns.

    Arguments:
        patterns (list): A list of wildcard pattern. e.g. ``["*.py",
            "*.pyc"]``
        case_sensitive (bool): If ``True``, then the callable will be case
            sensitive, otherwise it will be case insensitive.
        accept_prefix (bool): If ``True``, the name is
            not required to match the patterns themselves
            but only need to be a prefix of a string that does.

    Returns:
        callable: a matcher that will return `True` if the paths given as
        an argument matches any of the given patterns, or if no patterns
        exist.

    Example:
        >>> from fs import glob
        >>> is_python = glob.get_matcher(['*.py'], True)
        >>> is_python('__init__.py')
        True
        >>> is_python('foo.txt')
        False

    """
    if not patterns:
        return lambda path: True

    if accept_prefix:
        new_patterns = []
        for pattern in patterns:
            split = _split_pattern_by_sep(pattern)
            for i in range(1, len(split)):
                new_pattern = "/".join(split[:i])
                new_patterns.append(new_pattern)
                new_patterns.append(new_pattern + "/")
            new_patterns.append(pattern)
        patterns = new_patterns

    matcher = match_any if case_sensitive else imatch_any
    return partial(matcher, patterns)


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
            levels, re_pattern = _PATTERN_CACHE[(self.pattern, self.case_sensitive)]
        except KeyError:
            levels, re_str = _translate_glob(self.pattern)
            re_pattern = re.compile(re_str, 0 if self.case_sensitive else re.IGNORECASE)

        for path, info in self.fs.walk.info(
            path=self.path,
            namespaces=namespaces or self.namespaces,
            max_depth=levels,
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
