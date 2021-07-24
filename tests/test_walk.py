from __future__ import unicode_literals

import six
import unittest

from fs import walk
from fs.errors import FSError
from fs.memoryfs import MemoryFS
from fs.wrap import read_only


class TestWalker(unittest.TestCase):
    def setUp(self):
        self.walker = walk.Walker()

    def test_repr(self):
        repr(self.walker)

    def test_create(self):
        with self.assertRaises(ValueError):
            walk.Walker(ignore_errors=True, on_error=lambda path, error: True)
        walk.Walker(ignore_errors=True)

    def test_on_error_invalid(self):
        with self.assertRaises(TypeError):
            walk.Walker(on_error="nope")


class TestBoundWalkerBase(unittest.TestCase):
    def setUp(self):
        """
        Sets up the following file system with empty files:

        /
        -foo1/
        -    -top1.txt
        -    -top2.txt
        -foo2/
        -    -bar1/
        -    -bar2/
        -    -    -bar3/
        -    -    -    -test.txt
        -    -top3.bin
        -foo3/
        """
        self.fs = MemoryFS()

        self.fs.makedir("foo1")
        self.fs.makedir("foo2")
        self.fs.makedir("foo3")
        self.fs.create("foo1/top1.txt")
        self.fs.create("foo1/top2.txt")
        self.fs.makedir("foo1/bar1")
        self.fs.makedir("foo2/bar2")
        self.fs.makedir("foo2/bar2/bar3")
        self.fs.create("foo2/bar2/bar3/test.txt")
        self.fs.create("foo2/top3.bin")


class TestBoundWalker(TestBoundWalkerBase):
    def test_repr(self):
        repr(self.fs.walk)

    def test_readonly_wrapper_uses_same_walker(self):
        class CustomWalker(walk.Walker):
            @classmethod
            def bind(cls, fs):
                return walk.BoundWalker(fs, walker_class=CustomWalker)

        class CustomizedMemoryFS(MemoryFS):
            walker_class = CustomWalker

        base_fs = CustomizedMemoryFS()
        base_walker = base_fs.walk
        self.assertEqual(base_walker.walker_class, CustomWalker)

        readonly_fs = read_only(CustomizedMemoryFS())
        readonly_walker = readonly_fs.walk
        self.assertEqual(readonly_walker.walker_class, CustomWalker)


class TestWalk(TestBoundWalkerBase):
    def _walk_step_names(self, *args, **kwargs):
        """Performs a walk with the given arguments and returns a list of steps.

        Each step is a triple of the path, list of directory names, and list of file names.
        """
        _walk = []
        for step in self.fs.walk(*args, **kwargs):
            self.assertIsInstance(step, walk.Step)
            path, dirs, files = step
            _walk.append(
                (path, [info.name for info in dirs], [info.name for info in files])
            )
        return _walk

    def test_invalid_search(self):
        with self.assertRaises(ValueError):
            self.fs.walk(search="random")

    def test_walk_simple(self):
        _walk = self._walk_step_names()
        expected = [
            ("/", ["foo1", "foo2", "foo3"], []),
            ("/foo1", ["bar1"], ["top1.txt", "top2.txt"]),
            ("/foo2", ["bar2"], ["top3.bin"]),
            ("/foo3", [], []),
            ("/foo1/bar1", [], []),
            ("/foo2/bar2", ["bar3"], []),
            ("/foo2/bar2/bar3", [], ["test.txt"]),
        ]
        self.assertEqual(_walk, expected)

    def test_walk_filter(self):
        _walk = self._walk_step_names(filter=["top*.txt"])
        expected = [
            ("/", ["foo1", "foo2", "foo3"], []),
            ("/foo1", ["bar1"], ["top1.txt", "top2.txt"]),
            ("/foo2", ["bar2"], []),
            ("/foo3", [], []),
            ("/foo1/bar1", [], []),
            ("/foo2/bar2", ["bar3"], []),
            ("/foo2/bar2/bar3", [], []),
        ]
        self.assertEqual(_walk, expected)

    def test_walk_exclude(self):
        _walk = self._walk_step_names(exclude=["top*"])
        expected = [
            ("/", ["foo1", "foo2", "foo3"], []),
            ("/foo1", ["bar1"], []),
            ("/foo2", ["bar2"], []),
            ("/foo3", [], []),
            ("/foo1/bar1", [], []),
            ("/foo2/bar2", ["bar3"], []),
            ("/foo2/bar2/bar3", [], ["test.txt"]),
        ]
        self.assertEqual(_walk, expected)

    def test_walk_filter_dirs(self):
        _walk = self._walk_step_names(filter_dirs=["foo*"])
        expected = [
            ("/", ["foo1", "foo2", "foo3"], []),
            ("/foo1", [], ["top1.txt", "top2.txt"]),
            ("/foo2", [], ["top3.bin"]),
            ("/foo3", [], []),
        ]
        self.assertEqual(_walk, expected)

    def test_walk_filter_glob_1(self):
        _walk = self._walk_step_names(filter_glob=["/foo*/bar*/"])
        expected = [
            ("/", ["foo1", "foo2", "foo3"], []),
            ("/foo1", ["bar1"], []),
            ("/foo2", ["bar2"], []),
            ("/foo3", [], []),
            ("/foo1/bar1", [], []),
            ("/foo2/bar2", [], []),
        ]
        self.assertEqual(_walk, expected)

    def test_walk_filter_glob_2(self):
        _walk = self._walk_step_names(filter_glob=["/foo*/bar**"])
        expected = [
            ("/", ["foo1", "foo2", "foo3"], []),
            ("/foo1", ["bar1"], []),
            ("/foo2", ["bar2"], []),
            ("/foo3", [], []),
            ("/foo1/bar1", [], []),
            ("/foo2/bar2", ["bar3"], []),
            ("/foo2/bar2/bar3", [], ["test.txt"]),
        ]
        self.assertEqual(_walk, expected)

    def test_walk_filter_mix(self):
        _walk = self._walk_step_names(filter_glob=["/foo2/bar**"], filter=["top1.txt"])
        expected = [
            ("/", ["foo2"], []),
            ("/foo2", ["bar2"], []),
            ("/foo2/bar2", ["bar3"], []),
            ("/foo2/bar2/bar3", [], []),
        ]
        self.assertEqual(_walk, expected)

    def test_walk_exclude_dirs(self):
        _walk = self._walk_step_names(exclude_dirs=["bar*", "foo2"])
        expected = [
            ("/", ["foo1", "foo3"], []),
            ("/foo1", [], ["top1.txt", "top2.txt"]),
            ("/foo3", [], []),
        ]
        self.assertEqual(_walk, expected)

    def test_walk_exclude_glob(self):
        _walk = self._walk_step_names(exclude_glob=["**/top*", "test.txt"])
        expected = [
            ("/", ["foo1", "foo2", "foo3"], []),
            ("/foo1", ["bar1"], []),
            ("/foo2", ["bar2"], []),
            ("/foo3", [], []),
            ("/foo1/bar1", [], []),
            ("/foo2/bar2", ["bar3"], []),
            ("/foo2/bar2/bar3", [], ["test.txt"]),
        ]
        self.assertEqual(_walk, expected)

    def test_walk_depth(self):
        _walk = self._walk_step_names(search="depth")
        expected = [
            ("/foo1/bar1", [], []),
            ("/foo1", ["bar1"], ["top1.txt", "top2.txt"]),
            ("/foo2/bar2/bar3", [], ["test.txt"]),
            ("/foo2/bar2", ["bar3"], []),
            ("/foo2", ["bar2"], ["top3.bin"]),
            ("/foo3", [], []),
            ("/", ["foo1", "foo2", "foo3"], []),
        ]
        self.assertEqual(_walk, expected)

    def test_walk_path(self):
        _walk = self._walk_step_names("foo2")
        expected = [
            ("/foo2", ["bar2"], ["top3.bin"]),
            ("/foo2/bar2", ["bar3"], []),
            ("/foo2/bar2/bar3", [], ["test.txt"]),
        ]
        self.assertEqual(_walk, expected)

    def test_walk_max_depth_1_breadth(self):
        _walk = self._walk_step_names(max_depth=1, search="breadth")
        expected = [
            ("/", ["foo1", "foo2", "foo3"], []),
        ]
        self.assertEqual(_walk, expected)

    def test_walk_max_depth_1_depth(self):
        _walk = self._walk_step_names(max_depth=1, search="depth")
        expected = [
            ("/", ["foo1", "foo2", "foo3"], []),
        ]
        self.assertEqual(_walk, expected)

    def test_walk_max_depth_2(self):
        _walk = self._walk_step_names(max_depth=2)
        expected = [
            ("/", ["foo1", "foo2", "foo3"], []),
            ("/foo1", ["bar1"], ["top1.txt", "top2.txt"]),
            ("/foo2", ["bar2"], ["top3.bin"]),
            ("/foo3", [], []),
        ]
        self.assertEqual(_walk, expected)


class TestDirs(TestBoundWalkerBase):
    def test_walk_dirs(self):
        dirs = list(self.fs.walk.dirs())
        self.assertEqual(
            dirs,
            ["/foo1", "/foo2", "/foo3", "/foo1/bar1", "/foo2/bar2", "/foo2/bar2/bar3"],
        )

        dirs = list(self.fs.walk.dirs(search="depth"))
        self.assertEqual(
            dirs,
            ["/foo1/bar1", "/foo1", "/foo2/bar2/bar3", "/foo2/bar2", "/foo2", "/foo3"],
        )

        dirs = list(self.fs.walk.dirs(search="depth", exclude_dirs=["foo2"]))
        self.assertEqual(dirs, ["/foo1/bar1", "/foo1", "/foo3"])

    def test_foo(self):
        dirs = list(self.fs.walk.dirs(search="depth", exclude_dirs=["foo2"]))
        self.assertEqual(dirs, ["/foo1/bar1", "/foo1", "/foo3"])


class TestFiles(TestBoundWalkerBase):
    def test_walk_files(self):
        files = list(self.fs.walk.files())

        self.assertEqual(
            files,
            [
                "/foo1/top1.txt",
                "/foo1/top2.txt",
                "/foo2/top3.bin",
                "/foo2/bar2/bar3/test.txt",
            ],
        )

        files = list(self.fs.walk.files(search="depth"))
        self.assertEqual(
            files,
            [
                "/foo1/top1.txt",
                "/foo1/top2.txt",
                "/foo2/bar2/bar3/test.txt",
                "/foo2/top3.bin",
            ],
        )

    def test_walk_files_filter(self):
        files = list(self.fs.walk.files(filter=["*.txt"]))

        self.assertEqual(
            files, ["/foo1/top1.txt", "/foo1/top2.txt", "/foo2/bar2/bar3/test.txt"]
        )

        files = list(self.fs.walk.files(search="depth", filter=["*.txt"]))
        self.assertEqual(
            files, ["/foo1/top1.txt", "/foo1/top2.txt", "/foo2/bar2/bar3/test.txt"]
        )

        files = list(self.fs.walk.files(filter=["*.bin"]))

        self.assertEqual(files, ["/foo2/top3.bin"])

        files = list(self.fs.walk.files(filter=["*.nope"]))

        self.assertEqual(files, [])

    def test_walk_files_filter_glob(self):
        files = list(self.fs.walk.files(filter_glob=["/foo2/**"]))
        self.assertEqual(
            files,
            [
                "/foo2/top3.bin",
                "/foo2/bar2/bar3/test.txt",
            ],
        )

    def test_walk_files_exclude(self):
        # Test exclude argument works
        files = list(self.fs.walk.files(exclude=["*.txt"]))
        self.assertEqual(files, ["/foo2/top3.bin"])

        # Test exclude doesn't break filter
        files = list(self.fs.walk.files(filter=["*.bin"], exclude=["*.txt"]))
        self.assertEqual(files, ["/foo2/top3.bin"])

        # Test excluding everything
        files = list(self.fs.walk.files(exclude=["*"]))
        self.assertEqual(files, [])

    def test_broken(self):
        original_scandir = self.fs.scandir

        def broken_scandir(path, namespaces=None):
            if path == "/foo2":
                raise FSError("can't read dir")
            return original_scandir(path, namespaces=namespaces)

        self.fs.scandir = broken_scandir

        files = list(self.fs.walk.files(search="depth", ignore_errors=True))
        self.assertEqual(files, ["/foo1/top1.txt", "/foo1/top2.txt"])

        with self.assertRaises(FSError):
            list(self.fs.walk.files(on_error=lambda path, error: False))

    def test_subdir_uses_same_walker(self):
        class CustomWalker(walk.Walker):
            @classmethod
            def bind(cls, fs):
                return walk.BoundWalker(fs, walker_class=CustomWalker)

        class CustomizedMemoryFS(MemoryFS):
            walker_class = CustomWalker

        base_fs = CustomizedMemoryFS()
        base_fs.writetext("a", "a")
        base_fs.makedirs("b")
        base_fs.writetext("b/c", "c")
        base_fs.writetext("b/d", "d")
        base_walker = base_fs.walk
        self.assertEqual(base_walker.walker_class, CustomWalker)
        six.assertCountEqual(self, ["/a", "/b/c", "/b/d"], base_walker.files())

        sub_fs = base_fs.opendir("b")
        sub_walker = sub_fs.walk
        self.assertEqual(sub_walker.walker_class, CustomWalker)
        six.assertCountEqual(self, ["/c", "/d"], sub_walker.files())

    def test_check_file_overwrite(self):
        class CustomWalker(walk.Walker):
            def check_file(self, fs, info):
                return False

        walker = CustomWalker()
        files = list(walker.files(self.fs))
        self.assertEqual(files, [])


class TestInfo(TestBoundWalkerBase):
    def test_walk_info(self):
        walk = []
        for path, info in self.fs.walk.info():
            walk.append((path, info.is_dir, info.name))

        expected = [
            ("/foo1", True, "foo1"),
            ("/foo2", True, "foo2"),
            ("/foo3", True, "foo3"),
            ("/foo1/top1.txt", False, "top1.txt"),
            ("/foo1/top2.txt", False, "top2.txt"),
            ("/foo1/bar1", True, "bar1"),
            ("/foo2/bar2", True, "bar2"),
            ("/foo2/top3.bin", False, "top3.bin"),
            ("/foo2/bar2/bar3", True, "bar3"),
            ("/foo2/bar2/bar3/test.txt", False, "test.txt"),
        ]
        self.assertEqual(walk, expected)
