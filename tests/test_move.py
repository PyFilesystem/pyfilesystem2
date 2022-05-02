from __future__ import unicode_literals

import unittest

try:
    from unittest import mock
except ImportError:
    import mock

from parameterized import parameterized, parameterized_class

import fs.move
from fs import open_fs
from fs.errors import FSError, ResourceReadOnly
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

        self.assertTrue(src_fs.isempty("/"))
        self.assertTrue(dst_fs.isdir("foo/bar"))
        self.assertTrue(dst_fs.isfile("test.txt"))
        self.assertTrue(dst_fs.isfile("foo/bar/baz.txt"))

        if self.preserve_time:
            dst_file1_info = dst_fs.getinfo("test.txt", namespaces)
            dst_file2_info = dst_fs.getinfo("foo/bar/baz.txt", namespaces)
            self.assertEqual(dst_file1_info.modified, src_file1_info.modified)
            self.assertEqual(dst_file2_info.modified, src_file2_info.modified)

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

            if self.preserve_time:
                dst_fs_file_info = dst_fs.getinfo("dest.txt", namespaces)
                self.assertEqual(src_fs_file_info.modified, dst_fs_file_info.modified)

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

        self.assertFalse(src_fs.exists("foo"))
        self.assertTrue(src_fs.isfile("test.txt"))
        self.assertTrue(dst_fs.isdir("bar"))
        self.assertTrue(dst_fs.isfile("bar/baz.txt"))

        if self.preserve_time:
            dst_file2_info = dst_fs.getinfo("bar/baz.txt", namespaces)
            self.assertEqual(dst_file2_info.modified, src_file2_info.modified)


class TestMove(unittest.TestCase):
    def test_move_file_tempfs(self):
        with open_fs("temp://") as src, open_fs("temp://") as dst:
            src_dir = src.makedir("Some subfolder")
            src_dir.writetext("file.txt", "Content")
            dst_dir = dst.makedir("dest dir")
            fs.move.move_file(src_dir, "file.txt", dst_dir, "target.txt")
            self.assertFalse(src.exists("Some subfolder/file.txt"))
            self.assertEqual(dst.readtext("dest dir/target.txt"), "Content")

    def test_move_file_fs_urls(self):
        # create a temp dir to work on
        with open_fs("temp://") as tmp:
            path = tmp.getsyspath("/")
            tmp.makedir("subdir_src")
            tmp.writetext("subdir_src/file.txt", "Content")
            tmp.makedir("subdir_dst")
            fs.move.move_file(
                "osfs://" + join(path, "subdir_src"),
                "file.txt",
                "osfs://" + join(path, "subdir_dst"),
                "target.txt",
            )
            self.assertFalse(tmp.exists("subdir_src/file.txt"))
            self.assertEqual(tmp.readtext("subdir_dst/target.txt"), "Content")

    def test_move_file_same_fs_read_only_source(self):
        with open_fs("temp://") as tmp:
            path = tmp.getsyspath("/")
            tmp.writetext("file.txt", "Content")
            src = read_only(open_fs(path))
            dst = tmp.makedir("sub")
            with self.assertRaises(ResourceReadOnly):
                fs.move.move_file(src, "file.txt", dst, "target_file.txt")
            self.assertTrue(src.exists("file.txt"))
            self.assertFalse(
                dst.exists("target_file.txt"), "file should not have been copied over"
            )

    def test_move_file_read_only_mem_source(self):
        with open_fs("mem://") as src, open_fs("mem://") as dst:
            src.writetext("file.txt", "Content")
            dst_sub = dst.makedir("sub")
            src_ro = read_only(src)
            with self.assertRaises(ResourceReadOnly):
                fs.move.move_file(src_ro, "file.txt", dst_sub, "target.txt")
            self.assertTrue(src.exists("file.txt"))
            self.assertFalse(
                dst_sub.exists("target.txt"), "file should not have been copied over"
            )

    def test_move_file_read_only_mem_dest(self):
        with open_fs("mem://") as src, open_fs("mem://") as dst:
            src.writetext("file.txt", "Content")
            dst_ro = read_only(dst)
            with self.assertRaises(ResourceReadOnly):
                fs.move.move_file(src, "file.txt", dst_ro, "target.txt")
            self.assertTrue(src.exists("file.txt"))
            self.assertFalse(
                dst_ro.exists("target.txt"), "file should not have been copied over"
            )

    @parameterized.expand([(True,), (False,)])
    def test_move_file_cleanup_on_error(self, cleanup):
        with open_fs("mem://") as src, open_fs("mem://") as dst:
            src.writetext("file.txt", "Content")
            with mock.patch.object(src, "remove") as mck:
                mck.side_effect = FSError
                with self.assertRaises(FSError):
                    fs.move.move_file(
                        src,
                        "file.txt",
                        dst,
                        "target.txt",
                        cleanup_dst_on_error=cleanup,
                    )
            self.assertTrue(src.exists("file.txt"))
            self.assertEqual(not dst.exists("target.txt"), cleanup)
