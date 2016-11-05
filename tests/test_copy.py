from __future__ import unicode_literals

import unittest

import fs.copy
from fs import open_fs


class TestCopy(unittest.TestCase):

    def test_copy_fs(self):
        src_fs = open_fs('mem://')
        src_fs.makedirs('foo/bar')
        src_fs.makedirs('foo/empty')
        src_fs.touch('test.txt')
        src_fs.touch('foo/bar/baz.txt')

        dst_fs = open_fs('mem://')
        fs.copy.copy_fs(src_fs, dst_fs)

        self.assertTrue(dst_fs.isdir('foo/empty'))
        self.assertTrue(dst_fs.isdir('foo/bar'))
        self.assertTrue(dst_fs.isfile('test.txt'))

    def test_copy_dir(self):
        src_fs = open_fs('mem://')
        src_fs.makedirs('foo/bar')
        src_fs.makedirs('foo/empty')
        src_fs.touch('test.txt')
        src_fs.touch('foo/bar/baz.txt')

        dst_fs = open_fs('mem://')
        fs.copy.copy_dir(src_fs, '/foo', dst_fs, '/')

        self.assertTrue(dst_fs.isdir('bar'))
        self.assertTrue(dst_fs.isdir('empty'))
        self.assertTrue(dst_fs.isfile('bar/baz.txt'))