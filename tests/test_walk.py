from __future__ import unicode_literals

import unittest

from fs.errors import FSError
from fs.memoryfs import MemoryFS
from fs import walk


class TestWalk(unittest.TestCase):

    def setUp(self):
        self.fs = MemoryFS()

        self.fs.makedir('foo1')
        self.fs.makedir('foo2')
        self.fs.makedir('foo3')
        self.fs.create('foo1/top1.txt')
        self.fs.create('foo1/top2.txt')
        self.fs.makedir('foo1/bar1')
        self.fs.makedir('foo2/bar2')
        self.fs.makedir('foo2/bar2/bar3')
        self.fs.create('foo2/bar2/bar3/test.txt')
        self.fs.create('foo2/top3.txt')

    def test_invalid(self):
        with self.assertRaises(ValueError):
            walk.walk(self.fs, search='random')

    def test_walk_files(self):
        files = list(walk.walk_files(self.fs))

        self.assertEqual(
            files,
            [
                '/foo1/top1.txt',
                '/foo1/top2.txt',
                '/foo2/top3.txt',
                '/foo2/bar2/bar3/test.txt',
            ]
        )

        files = list(walk.walk_files(self.fs, search="depth"))
        print(repr(files))

        self.assertEqual(
            files,
            [
                '/foo1/top1.txt',
                '/foo1/top2.txt',
                '/foo2/bar2/bar3/test.txt',
                '/foo2/top3.txt',
            ]
        )

    def test_walk_dirs(self):
        dirs = list(walk.walk_dirs(self.fs))
        self.assertEqual(
            dirs,
            [
                '/foo1',
                '/foo2',
                '/foo3',
                '/foo1/bar1',
                '/foo2/bar2',
                '/foo2/bar2/bar3'
            ]
        )

        dirs = list(walk.walk_dirs(self.fs, search="depth"))
        self.assertEqual(
            dirs,
            [
                '/foo1/bar1',
                '/foo2/bar2/bar3',
                '/foo2/bar2',
                '/foo1',
                '/foo2',
                '/foo3'
            ]
        )

    def test_broken(self):
        original_scandir = self.fs.scandir

        def broken_scandir(path, namespaces=None):
            if path == '/foo2':
                raise FSError("can't read dir")
            return original_scandir(path, namespaces=namespaces)

        self.fs.scandir = broken_scandir

        files = list(walk.walk_files(self.fs, search="depth"))
        self.assertEqual(
            files,
            [
                '/foo1/top1.txt',
                '/foo1/top2.txt'
            ]
        )

        with self.assertRaises(FSError):
            list(
                walk.walk_files(
                    self.fs,
                    on_error=lambda path, error: False
                )
            )
