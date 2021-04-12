from __future__ import unicode_literals

import unittest

from parameterized import parameterized_class

import fs.move
from fs import open_fs


@parameterized_class(("preserve_time",), [(True,), (False,)])
class TestMove(unittest.TestCase):
    def test_move_fs(self):
        namespaces = ("details", "modified")

        src_fs = open_fs("mem://")
        src_fs.makedirs("foo/bar")
        src_fs.touch("test.txt")
        src_fs.touch("foo/bar/baz.txt")
        src_file1_info = src_fs.getinfo("test.txt", namespaces)
        src_file2_info = src_fs.getinfo("foo/bar/baz.txt", namespaces)

        dst_fs = open_fs("mem://")
        dst_fs.create("test.txt")
        dst_fs.setinfo("test.txt", {"details": {"modified": 1000000}})

        fs.move.move_fs(src_fs, dst_fs, preserve_time=self.preserve_time)

        self.assertTrue(dst_fs.isdir("foo/bar"))
        self.assertTrue(dst_fs.isfile("test.txt"))
        self.assertTrue(dst_fs.isfile("foo/bar/baz.txt"))
        self.assertTrue(src_fs.isempty("/"))

        if self.preserve_time:
            dst_file1_info = dst_fs.getinfo("test.txt", namespaces)
            dst_file2_info = dst_fs.getinfo("foo/bar/baz.txt", namespaces)
            self.assertEqual(dst_file1_info.modified, src_file1_info.modified)
            self.assertEqual(dst_file2_info.modified, src_file2_info.modified)

    def test_move_dir(self):
        namespaces = ("details", "modified")

        src_fs = open_fs("mem://")
        src_fs.makedirs("foo/bar")
        src_fs.touch("test.txt")
        src_fs.touch("foo/bar/baz.txt")
        src_file2_info = src_fs.getinfo("foo/bar/baz.txt", namespaces)

        dst_fs = open_fs("mem://")
        dst_fs.create("test.txt")
        dst_fs.setinfo("test.txt", {"details": {"modified": 1000000}})

        fs.move.move_dir(src_fs, "/foo", dst_fs, "/", preserve_time=self.preserve_time)

        self.assertTrue(dst_fs.isdir("bar"))
        self.assertTrue(dst_fs.isfile("bar/baz.txt"))
        self.assertFalse(src_fs.exists("foo"))
        self.assertTrue(src_fs.isfile("test.txt"))

        if self.preserve_time:
            dst_file2_info = dst_fs.getinfo("bar/baz.txt", namespaces)
            self.assertEqual(dst_file2_info.modified, src_file2_info.modified)
