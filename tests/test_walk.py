from __future__ import unicode_literals

import unittest

from fs.errors import FSError
from fs.memoryfs import MemoryFS
from fs import walk


class TestWalkerBase(unittest.TestCase):

    def test_not_implemented(self):
        walker = walk.WalkerBase()
        with self.assertRaises(NotImplementedError):
            walker.walk(None, path='/')


class TestWalker(unittest.TestCase):

    def setUp(self):
        self.walker = walk.Walker()

    def test_repr(self):
        repr(self.walker)

    def test_create(self):
        with self.assertRaises(AssertionError):
            walk.Walker(ignore_errors=True, on_error=lambda path, error: True)
        walk.Walker(ignore_errors=True)


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
            self.fs.walk(search='random')

    def test_repr(self):
        repr(self.fs.walk)

    def test_walk(self):
        walk = []
        for path, dirs, files in self.fs.walk():
            walk.append((
                path,
                [info.name for info in dirs],
                [info.name for info in files]
            ))
        expected = [(u'/', [u'foo1', u'foo2', u'foo3'], []), (u'/foo1', [u'bar1'], [u'top1.txt', u'top2.txt']), (u'/foo2', [u'bar2'], [u'top3.txt']), (u'/foo3', [], []), (u'/foo1/bar1', [], []), (u'/foo2/bar2', [u'bar3'], []), (u'/foo2/bar2/bar3', [], [u'test.txt'])]
        self.assertEqual(walk, expected)

    def test_walk_files(self):
        files = list(self.fs.walk.files())

        self.assertEqual(
            files,
            [
                '/foo1/top1.txt',
                '/foo1/top2.txt',
                '/foo2/top3.txt',
                '/foo2/bar2/bar3/test.txt',
            ]
        )

        files = list(self.fs.walk.files(search="depth"))
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
        dirs = list(self.fs.walk.dirs())
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

        dirs = list(self.fs.walk.dirs(search="depth"))
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

        dirs = list(self.fs.walk.dirs(search="depth", exclude_dirs=['foo2']))
        self.assertEqual(
            dirs,
            [
                '/foo1/bar1',
                '/foo1',
                '/foo3'
            ]
        )

    def test_walk_info(self):
        walk = []
        for path, info in self.fs.walk.info():
            walk.append((path, info.is_dir, info.name))
        expected = [(u'/foo1', True, u'foo1'), (u'/foo2', True, u'foo2'), (u'/foo3', True, u'foo3'), (u'/foo1/bar1', True, u'bar1'), (u'/foo1/top1.txt', False, u'top1.txt'), (u'/foo1/top2.txt', False, u'top2.txt'), (u'/foo2/bar2', True, u'bar2'), (u'/foo2/top3.txt', False, u'top3.txt'), (u'/foo2/bar2/bar3', True, u'bar3'), (u'/foo2/bar2/bar3/test.txt', False, u'test.txt')]
        self.assertEqual(walk, expected)

    def test_broken(self):
        original_scandir = self.fs.scandir

        def broken_scandir(path, namespaces=None):
            if path == '/foo2':
                raise FSError("can't read dir")
            return original_scandir(path, namespaces=namespaces)

        self.fs.scandir = broken_scandir

        files = list(self.fs.walk.files(search="depth"))
        self.assertEqual(
            files,
            [
                '/foo1/top1.txt',
                '/foo1/top2.txt'
            ]
        )

        with self.assertRaises(FSError):
            list(
                self.fs.walk.files(
                    on_error=lambda path, error: False
                )
            )
