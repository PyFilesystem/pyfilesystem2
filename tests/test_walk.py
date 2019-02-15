from __future__ import unicode_literals

import unittest

from fs.errors import FSError
from fs.memoryfs import MemoryFS
from fs import walk
from fs.wrap import read_only
import six


class TestWalker(unittest.TestCase):
    def setUp(self):
        self.walker = walk.Walker()

    def test_repr(self):
        repr(self.walker)

    def test_create(self):
        with self.assertRaises(ValueError):
            walk.Walker(ignore_errors=True, on_error=lambda path, error: True)
        walk.Walker(ignore_errors=True)


class TestWalk(unittest.TestCase):
    def setUp(self):
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

    def test_invalid(self):
        with self.assertRaises(ValueError):
            self.fs.walk(search="random")

    def test_repr(self):
        repr(self.fs.walk)

    def test_walk(self):
        _walk = []
        for step in self.fs.walk():
            self.assertIsInstance(step, walk.Step)
            path, dirs, files = step
            _walk.append(
                (path, [info.name for info in dirs], [info.name for info in files])
            )
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

    def test_walk_filter_dirs(self):
        _walk = []
        for step in self.fs.walk(filter_dirs=["foo*"]):
            self.assertIsInstance(step, walk.Step)
            path, dirs, files = step
            _walk.append(
                (path, [info.name for info in dirs], [info.name for info in files])
            )
        expected = [
            ("/", ["foo1", "foo2", "foo3"], []),
            ("/foo1", [], ["top1.txt", "top2.txt"]),
            ("/foo2", [], ["top3.bin"]),
            ("/foo3", [], []),
        ]
        self.assertEqual(_walk, expected)

    def test_walk_depth(self):
        _walk = []
        for step in self.fs.walk(search="depth"):
            self.assertIsInstance(step, walk.Step)
            path, dirs, files = step
            _walk.append(
                (path, [info.name for info in dirs], [info.name for info in files])
            )
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

    def test_walk_directory(self):
        _walk = []
        for step in self.fs.walk("foo2"):
            self.assertIsInstance(step, walk.Step)
            path, dirs, files = step
            _walk.append(
                (path, [info.name for info in dirs], [info.name for info in files])
            )
        expected = [
            ("/foo2", ["bar2"], ["top3.bin"]),
            ("/foo2/bar2", ["bar3"], []),
            ("/foo2/bar2/bar3", [], ["test.txt"]),
        ]
        self.assertEqual(_walk, expected)

    def test_walk_levels_1(self):
        results = list(self.fs.walk(max_depth=1))
        self.assertEqual(len(results), 1)
        dirs = sorted(info.name for info in results[0].dirs)
        self.assertEqual(dirs, ["foo1", "foo2", "foo3"])
        files = sorted(info.name for info in results[0].files)
        self.assertEqual(files, [])

    def test_walk_levels_1_depth(self):
        results = list(self.fs.walk(max_depth=1, search="depth"))
        self.assertEqual(len(results), 1)
        dirs = sorted(info.name for info in results[0].dirs)
        self.assertEqual(dirs, ["foo1", "foo2", "foo3"])
        files = sorted(info.name for info in results[0].files)
        self.assertEqual(files, [])

    def test_walk_levels_2(self):
        _walk = []
        for step in self.fs.walk(max_depth=2):
            self.assertIsInstance(step, walk.Step)
            path, dirs, files = step
            _walk.append(
                (
                    path,
                    sorted(info.name for info in dirs),
                    sorted(info.name for info in files),
                )
            )
        expected = [
            ("/", ["foo1", "foo2", "foo3"], []),
            ("/foo1", ["bar1"], ["top1.txt", "top2.txt"]),
            ("/foo2", ["bar2"], ["top3.bin"]),
            ("/foo3", [], []),
        ]
        self.assertEqual(_walk, expected)

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

    def test_on_error_invalid(self):
        with self.assertRaises(TypeError):
            walk.Walker(on_error="nope")

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
