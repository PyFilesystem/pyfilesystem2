from __future__ import unicode_literals

import re

from ._repr import make_repr
from . import path
from . import wildcard


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
        re.compile(re_glob, re.IGNORECASE if case_sensitive else None),
    )


def _glob(fs, pattern, path="/", namespaces=None, case_sensitive=True):
    levels, recursive, _re_glob = _translate_glob(
        pattern, case_sensitive=case_sensitive
    )
    for path, info in fs.walk.info(
        path=path, namespaces=namespaces, max_depth=None if recursive else levels
    ):
        if info.is_dir:
            path += "/"
        if _re_glob.match(path):
            yield path, info


class GlobGenerator(object):
    def __init__(self, fs, pattern, path='/', namespaces=None, case_sensitive=True):
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
            path=(self.path, '/'),
            namespaces=(self.namespaces, None),
            case_sensitive=(self.case_sensitive, True),
        )

    def __iter__(self):
        for path, info in _glob(
            self.fs,
            self.pattern,
            path=self.path,
            namespaces=self.namespaces,
            case_sensitive=self.case_sensitive,
        ):
            yield path, info

    def count(self):
        size = 0
        for path, info in _glob(
            self.fs,
            self.pattern,
            path=self.path,
            namespaces=['details'],
            case_sensitive=self.case_sensitive,
        ):
            size += info.size
        return size


class Globber(object):

    __slots__ = ["fs"]

    def __init__(self, fs):
        self.fs = fs

    def __repr__(self):
        return make_repr(self.__class__.__name__, self.fs)

    def __call__(self, pattern, path="/", namespaces=None, case_sensitive=True):
        return GlobGenerator(self.fs, pattern, path, namespaces, case_sensitive)


if __name__ == "__main__":

    from fs import open_fs

    m = open_fs("~/projects/moya")

    print(m.glob)

    print(m.glob('*.py'))

    for info, path in m.glob('*/*.py'):
        print(info)

    print(m.glob('**/*.py').count())

