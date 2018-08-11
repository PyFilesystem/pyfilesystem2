from __future__ import unicode_literals

from collections import namedtuple
import re

from .lrucache import LRUCache
from ._repr import make_repr
from . import path
from . import wildcard


_PATTERN_CACHE = LRUCache(
    1000
)  # type: LRUCache[Tuple[Text, bool], Tuple[int, bool, Pattern]]


Counts = namedtuple("Counts", ["files", "directories", "data"])
LineCounts = namedtuple("LineCounts", ["lines", "non_blank"])

if False:  # typing.TYPE_CHECKING
    from typing import Iterator, List, Optional, Tuple
    from .base import FS
    from .info import Info


def _translate_glob(pattern, case_sensitive=True):
    levels = 0
    recursive = False
    re_patterns = [""]
    for component in path.iteratepath(pattern):
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
    try:
        levels, recursive, re_pattern = _PATTERN_CACHE[(pattern, True)]
    except KeyError:
        levels, recursive, re_pattern = _translate_glob(pattern, case_sensitive=True)
        _PATTERN_CACHE[(pattern, True)] = (levels, recursive, re_pattern)
    return bool(re_pattern.match(path))


def imatch(pattern, path):
    try:
        levels, recursive, re_pattern = _PATTERN_CACHE[(pattern, False)]
    except KeyError:
        levels, recursive, re_pattern = _translate_glob(pattern, case_sensitive=True)
        _PATTERN_CACHE[(pattern, False)] = (levels, recursive, re_pattern)
    return bool(re_pattern.match(path))


class Globber(object):
    """A generator of glob results.

        Arguments:
            fs (~fs.base.FS): A filesystem object
            pattern (str): A glob pattern, e.g. ``"**/*.py"`
            namespaces (list): A list of additional info namespaces.
            case_sensitive (bool): If ``True``, the path matching will be
                case *sensitive* i.e. ``"FOO.py"`` and ``"foo.py"`` will
                be different, otherwise path matching will be case *insensitive*.
            exclude_dirs (list): A list of patterns to exclude when searching,
                e.g. ``["*.git"]``.

    """

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
                yield path, info

    def __iter__(self):
        # type: () -> Iterator[Tuple[str, Info]]
        return self._make_iter()

    def count(self):
        """Count files / directories / data in matched paths.

        Example::

            counts = Globber(my_fs, '*.py').counts()
            print(f"files={counts.files}")
            print(f"directories={counts.directories}")
            print(f"data={count.data} bytes")

        Returns:
            `~Counts`: A named tuple containing results.



        """
        # type: () -> Counts
        directories = 0
        files = 0
        data = 0
        for path, info in self._make_iter(namespaces=["details"]):
            if info.is_dir:
                directories += 1
            else:
                files += 1
            data += info.size
        return Counts(directories=directories, files=files, data=data)

    def count_lines(self):
        # type: () -> LineCounts
        lines = 0
        non_blank = 0
        for path, info in self._make_iter():
            if info.is_file:
                for line in self.fs.open(path):
                    lines += 1
                    if line.rstrip():
                        non_blank += 1
        return LineCounts(lines=lines, non_blank=non_blank)

    def remove(self):
        # type: () -> int
        removes = 0
        for path, info in self._make_iter(search="depth"):
            if info.is_dir:
                self.fs.removetree(path)
            else:
                self.fs.remove(path)
            removes += 1
        return removes


class BoundGlobber(object):
    """An object which searches a filesystem for paths matching a *glob*
    pattern.

    Arguments:
        fs (FS): A filesystem object.

    """
    __slots__ = ["fs"]

    def __init__(self, fs):
        # type: (FS) -> None
        self.fs = fs

    def __repr__(self):
        return make_repr(self.__class__.__name__, self.fs)

    def __call__(
        self, pattern, path="/", namespaces=None, case_sensitive=True, exclude_dirs=None
    ):
        """A generator of glob results.

        Arguments:
            pattern (str): A glob pattern, e.g. ``"**/*.py"``
            namespaces (list): A list of additional info namespaces.
            case_sensitive (bool): If ``True``, the path matching will be
                case *sensitive* i.e. ``"FOO.py"`` and ``"foo.py"`` will
                be different, otherwise path matching will be case **insensitive**.
            exclude_dirs (list): A list of patterns to exclude when searching,
                e.g. ``["*.git"]``.

        Returns:
            ~fs.flob.Globber: An object that may be iterated over,
                yielding tuples of ``(path, info)`` for matching paths.


        """
        # type: (str, str, Optional[List[str]], bool, Optional[List[str]]) -> Globber
        return GlobMatcher(
            self.fs,
            pattern,
            path,
            namespaces=namespaces,
            case_sensitive=case_sensitive,
            exclude_dirs=exclude_dirs,
        )
