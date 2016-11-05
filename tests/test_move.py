
from __future__ import unicode_literals

import unittest

import fs.move
from fs import open_fs


class TestMove(unittest.TestCase):

    def test_move_fs(self):
        src_fs = open_fs('mem://')
        src_fs.makedirs('foo/bar')
        src_fs.touch('test.txt')
        src_fs.touch('foo/bar/baz.txt')

        dst_fs = open_fs('mem://')
        fs.move.move_fs(src_fs, dst_fs)

        self.assertTrue(dst_fs.isdir('foo/bar'))
        self.assertTrue(dst_fs.isfile('test.txt'))
        self.assertTrue(src_fs.isempty('/'))

    def test_copy_dir(self):
        src_fs = open_fs('mem://')
        src_fs.makedirs('foo/bar')
        src_fs.touch('test.txt')
        src_fs.touch('foo/bar/baz.txt')

        dst_fs = open_fs('mem://')
        fs.move.move_dir(src_fs, '/foo', dst_fs, '/')

        self.assertTrue(dst_fs.isdir('bar'))
        self.assertTrue(dst_fs.isfile('bar/baz.txt'))
        self.assertFalse(src_fs.exists('foo'))