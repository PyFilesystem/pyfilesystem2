from __future__ import unicode_literals

import unittest

from parameterized import parameterized_class

import fs.move
from fs import open_fs
from fs.errors import ResourceReadOnly
from fs.path import join
from fs.wrap import read_only


@parameterized_class(("preserve_time",), [(True,), (False,)])
class TestMoveCheckTime(unittest.TestCase):
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

        dst_file1_info = dst_fs.getinfo("test.txt", namespaces)
        dst_file2_info = dst_fs.getinfo("foo/bar/baz.txt", namespaces)
        self.assertEqual(
            dst_file1_info.modified == src_file1_info.modified,
            self.preserve_time,
        )
        self.assertEqual(
            dst_file2_info.modified == src_file2_info.modified,
            self.preserve_time,
        )

    def test_move_file(self):
        namespaces = ("details", "modified")
        with open_fs("mem://") as src_fs, open_fs("mem://") as dst_fs:
            src_fs.writetext("source.txt", "Source")
            src_fs_file_info = src_fs.getinfo("source.txt", namespaces)
            fs.move.move_file(
                src_fs,
                "source.txt",
                dst_fs,
                "dest.txt",
                preserve_time=self.preserve_time,
            )
            self.assertFalse(src_fs.exists("source.txt"))
            self.assertEqual(dst_fs.readtext("dest.txt"), "Source")

            dst_fs_file_info = dst_fs.getinfo("dest.txt", namespaces)
            self.assertEqual(
                src_fs_file_info.modified == dst_fs_file_info.modified,
                self.preserve_time,
            )

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

        dst_file2_info = dst_fs.getinfo("bar/baz.txt", namespaces)
        self.assertEqual(
            dst_file2_info.modified == src_file2_info.modified, self.preserve_time
        )


class TestMove(unittest.TestCase):
    def test_move_file_tempfs(self):
        with open_fs("temp://") as a, open_fs("temp://") as b:
            dir_a = a.makedir("dir")
            dir_b = b.makedir("subdir")
            dir_b.writetext("file.txt", "Content")
            fs.move.move_file(dir_b, "file.txt", dir_a, "here.txt")
            self.assertEqual(a.readtext("dir/here.txt"), "Content")
            self.assertFalse(b.exists("subdir/file.txt"))

    def test_move_file_fs_urls(self):
        # create a temp dir to work on
        with open_fs("temp://") as tmp:
            path = tmp.getsyspath("/")
            tmp.writetext("file.txt", "Content")
            tmp.makedir("subdir")
            fs.move.move_file(
                "osfs://" + path,
                "file.txt",
                "osfs://" + join(path, "subdir"),
                "file.txt",
            )
            self.assertFalse(tmp.exists("file.txt"))
            self.assertEqual(tmp.readtext("subdir/file.txt"), "Content")

        with open_fs("mem://") as src, open_fs("mem://") as dst:
            src.writetext("source.txt", "Source")
            fs.move.move_file(src, "source.txt", dst, "dest.txt")
            self.assertFalse(src.exists("source.txt"))
            self.assertEqual(dst.readtext("dest.txt"), "Source")

    def test_move_file_same_fs_read_only_source(self):
        with open_fs("temp://") as tmp:
            path = tmp.getsyspath("/")
            tmp.writetext("file.txt", "Content")
            src = read_only(open_fs(path))
            dst = tmp.makedir("sub")
            with self.assertRaises(ResourceReadOnly):
                fs.move.move_file(src, "file.txt", dst, "file.txt")
            self.assertFalse(
                dst.exists("file.txt"), "file should not have been copied over"
            )
            self.assertTrue(src.exists("file.txt"))

    def test_move_file_read_only_mem_source(self):
        with open_fs("mem://") as src, open_fs("mem://") as dst:
            src.writetext("file.txt", "Content")
            sub = dst.makedir("sub")
            src_ro = read_only(src)
            with self.assertRaises(ResourceReadOnly):
                fs.move.move_file(src_ro, "file.txt", sub, "file.txt")
            self.assertFalse(
                sub.exists("file.txt"), "file should not have been copied over"
            )
            self.assertTrue(src.exists("file.txt"))

    def test_move_file_read_only_mem_dest(self):
        with open_fs("mem://") as src, open_fs("mem://") as dst:
            src.writetext("file.txt", "Content")
            dst_ro = read_only(dst)
            with self.assertRaises(ResourceReadOnly):
                fs.move.move_file(src, "file.txt", dst_ro, "file.txt")
            self.assertFalse(
                dst_ro.exists("file.txt"), "file should not have been copied over"
            )
            self.assertTrue(src.exists("file.txt"))

    def test_move_dir_cleanup(self):
        src_fs = open_fs("mem://")
        src_fs.makedirs("foo/bar")
        src_fs.touch("foo/bar/baz.txt")
        src_fs.touch("foo/test.txt")

        dst_fs = open_fs("mem://")
        dst_fs.create("test.txt")

        ro_src = read_only(src_fs)

        with self.assertRaises(ResourceReadOnly):
            fs.move.move_dir(ro_src, "/foo", dst_fs, "/")

        self.assertTrue(src_fs.exists("foo/bar/baz.txt"))
        self.assertTrue(src_fs.exists("foo/test.txt"))
        self.assertFalse(dst_fs.isdir("bar"))
        self.assertFalse(dst_fs.exists("bar/baz.txt"))
        self.assertTrue(dst_fs.exists("test.txt"))
