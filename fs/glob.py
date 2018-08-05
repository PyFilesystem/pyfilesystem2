from __future__ import unicode_literals

from collections import namedtuple
import re

from ._repr import make_repr
from . import path
from . import wildcard


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
    re_glob = (
        "(?ms)" + "".join(re_patterns) + ("/\Z" if pattern.endswith("/") else "\Z")
    )
    return (
        levels,
        recursive,
        re.compile(re_glob, 0 if case_sensitive else re.IGNORECASE),
    )


def _glob(fs, pattern, search="breadth", path="/", namespaces=None, case_sensitive=True):
    levels, recursive, _re_glob = _translate_glob(
        pattern, case_sensitive=case_sensitive
    )
    for path, info in fs.walk.info(
        path=path,
        namespaces=namespaces,
        max_depth=None if recursive else levels,
        search=search,
    ):
        if info.is_dir:
            path += "/"
        if _re_glob.match(path):
            yield path, info


class GlobGenerator(object):
    def __init__(self, fs, pattern, path="/", namespaces=None, case_sensitive=True):
        # type: (FS, str, str, Optional[List[str]], bool) -> None
        self.fs = fs
        self.pattern = pattern
        self.path = path
        self.namespaces = namespaces
        self.case_sensitive = case_sensitive

    def __repr__(self):
        return make_repr(
            self.__class__.__name__,
            self.fs,
            self.pattern,
            path=(self.path, "/"),
            namespaces=(self.namespaces, None),
            case_sensitive=(self.case_sensitive, True),
        )

    def _make_iter(self, search="breadth", namespaces=None):
        # type: (str) -> Iterator[str, Tuple[str, Info]]
        return _glob(
            self.fs,
            self.pattern,
            search=search,
            path=self.path,
            namespaces=namespaces or self.namespaces,
            case_sensitive=self.case_sensitive,
        )

    def __iter__(self):
        # type: () -> Iterator[Tuple[str, Info]]
        return self._make_iter()

    def files(self):
        # type: () -> Iterator[str]
        for path, info in self:
            if info.is_dir:
                yield path

    def dirs(self):
        # type: () -> Iterator[str]
        for path, info in self:
            if info.is_file:
                yield path

    def count(self):
        # type: () -> Counts
        directories = 0
        files = 0
        data = 0
        for path, info in self._make_iter(namespaces=['details']):
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
        for path, info in self._make_iter(search='depth'):
            if info.is_dir:
                self.fs.removetree(path)
            else:
                self.fs.remove(path)
            removes += 1
        return removes


class Globber(object):
    __slots__ = ["fs"]

    def __init__(self, fs):
        # type: (FS) -> None
        self.fs = fs

    def __repr__(self):
        return make_repr(self.__class__.__name__, self.fs)

    def __call__(self, pattern, path="/", namespaces=None, case_sensitive=True):
        # type: (str, str, Optional[List[str]], bool) -> GlobGenerator
        return GlobGenerator(self.fs, pattern, path, namespaces, case_sensitive)


if __name__ == "__main__":  # pragma: no cover

    from fs import open_fs

    m = open_fs("~/projects/moya")

    print(m.glob)

    print(m.glob("*.py"))

    for info, path in m.glob("*/*.py"):
        print(info)

    print(m.glob("**/*.py").count())

    print(m.glob("*/*.py").count_lines())

