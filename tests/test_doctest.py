# coding: utf-8
"""Test doctest contained tests in every file of the module.
"""
import doctest
import importlib
import os
import pkgutil
import tempfile
import time
import types
import unittest
import warnings
from pprint import pprint

try:
    from unittest import mock
except ImportError:
    import mock

import six

import fs
import fs.opener.parse
from fs.memoryfs import MemoryFS
from fs.subfs import ClosingSubFS

# --- Mocks ------------------------------------------------------------------


def _home_fs():
    """Create a mock filesystem that matches the XDG user-dirs spec."""
    home_fs = MemoryFS()
    home_fs.makedir("Desktop")
    home_fs.makedir("Documents")
    home_fs.makedir("Downloads")
    home_fs.makedir("Music")
    home_fs.makedir("Pictures")
    home_fs.makedir("Public")
    home_fs.makedir("Templates")
    home_fs.makedir("Videos")
    return home_fs


def _open_fs(path):
    """A mock `open_fs` that avoids side effects when running doctests."""
    if "://" not in path:
        path = "osfs://{}".format(path)
    parse_result = fs.opener.parse(path)
    if parse_result.protocol == "osfs" and parse_result.resource == "~":
        home_fs = _home_fs()
        if parse_result.path is not None:
            home_fs = home_fs.opendir(parse_result.path, factory=ClosingSubFS)
        return home_fs
    elif parse_result.protocol in {"ftp", "ftps", "mem", "temp"}:
        return MemoryFS()
    else:
        raise RuntimeError("not allowed in doctests: {}".format(path))


def _my_fs(module):
    """Create a mock filesystem to be used in examples."""
    my_fs = MemoryFS()
    if module == "fs.base":
        my_fs.makedir("Desktop")
        my_fs.makedir("Videos")
        my_fs.touch("Videos/starwars.mov")
        my_fs.touch("file.txt")
    elif module == "fs.info":
        my_fs.touch("foo.tar.gz")
        my_fs.settext("foo.py", "print('Hello, world!')")
        my_fs.makedir("bar")
    elif module in {"fs.walk", "fs.glob"}:
        my_fs.makedir("dir1")
        my_fs.makedir("dir2")
        my_fs.settext("foo.py", "print('Hello, world!')")
        my_fs.touch("foo.pyc")
        my_fs.settext("bar.py", "print('ok')\n\n# this is a comment\n")
        my_fs.touch("bar.pyc")
    return my_fs


def _open(filename, mode="r"):
    """A mock `open` that actually opens a temporary file."""
    return tempfile.NamedTemporaryFile(mode="r+" if mode == "r" else mode)


# --- Loader protocol --------------------------------------------------------


def _load_tests_from_module(tests, module, globs, setUp=None, tearDown=None):
    """Load tests from module, iterating through submodules."""
    for attr in (getattr(module, x) for x in dir(module) if not x.startswith("_")):
        if isinstance(attr, types.ModuleType):
            suite = doctest.DocTestSuite(
                attr,
                globs,
                setUp=setUp,
                tearDown=tearDown,
                optionflags=+doctest.ELLIPSIS,
            )
            tests.addTests(suite)
    return tests


def _load_tests(loader, tests, ignore):
    """`load_test` function used by unittest to find the doctests."""

    # NB (@althonos): we only test docstrings on Python 3 because it's
    # extremely hard to maintain compatibility for both versions without
    # extensively hacking `doctest` and `unittest`.
    if six.PY2:
        return tests

    def setUp(self):
        warnings.simplefilter("ignore")
        self._open_fs_mock = mock.patch.object(fs, "open_fs", new=_open_fs)
        self._open_fs_mock.__enter__()
        self._ftpfs_mock = mock.patch.object(fs.ftpfs, "FTPFS")
        self._ftpfs_mock.__enter__()

    def tearDown(self):
        self._open_fs_mock.__exit__(None, None, None)
        self._ftpfs_mock.__exit__(None, None, None)
        warnings.simplefilter(warnings.defaultaction)

    # recursively traverse all library submodules and load tests from them
    packages = [None, fs]
    for pkg in iter(packages.pop, None):
        for (_, subpkgname, subispkg) in pkgutil.walk_packages(pkg.__path__):
            # import the submodule and add it to the tests
            module = importlib.import_module(".".join([pkg.__name__, subpkgname]))

            # load some useful modules / classes / mocks to the
            # globals so that we don't need to explicitly import
            # them in the doctests
            globs = dict(**module.__dict__)
            globs.update(
                os=os,
                fs=fs,
                my_fs=_my_fs(module.__name__),
                open=_open,
                # NB (@althonos): This allows using OSFS in some examples,
                # while not actually opening the real filesystem
                OSFS=lambda path: MemoryFS(),
                # NB (@althonos): This is for compatibility in `fs.registry`
                print_list=lambda path: None,
                pprint=pprint,
                time=time,
            )

            # load the doctests into the unittest test suite
            tests.addTests(
                doctest.DocTestSuite(
                    module,
                    globs=globs,
                    setUp=setUp,
                    tearDown=tearDown,
                    optionflags=+doctest.ELLIPSIS,
                )
            )

            # if the submodule is a package, we need to process its submodules
            # as well, so we add it to the package queue
            if subispkg:
                packages.append(module)

    return tests


# --- Unit test wrapper ------------------------------------------------------
#
# NB (@althonos): Since pytest doesn't support the `load_tests` protocol
# above, we manually build a `unittest.TestCase` using a dedicated test
# method for each doctest. This should be safe to remove when pytest
# supports it, or if we move away from pytest to run tests.


class TestDoctest(unittest.TestCase):
    pass


def make_wrapper(x):
    def _test_wrapper(self):
        x.setUp()
        try:
            x.runTest()
        finally:
            x.tearDown()

    return _test_wrapper


for x in _load_tests(None, unittest.TestSuite(), False):
    setattr(TestDoctest, "test_{}".format(x.id().replace(".", "_")), make_wrapper(x))
