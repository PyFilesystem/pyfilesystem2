from __future__ import unicode_literals

import errno
import datetime
import os
import unittest
import tempfile
import shutil
import calendar

import fs.copy
from fs import open_fs


class TestCopy(unittest.TestCase):
    def test_copy_fs(self):
        for workers in (0, 1, 2, 4):
            src_fs = open_fs("mem://")
            src_fs.makedirs("foo/bar")
            src_fs.makedirs("foo/empty")
            src_fs.touch("test.txt")
            src_fs.touch("foo/bar/baz.txt")

            dst_fs = open_fs("mem://")
            fs.copy.copy_fs(src_fs, dst_fs, workers=workers)

            self.assertTrue(dst_fs.isdir("foo/empty"))
            self.assertTrue(dst_fs.isdir("foo/bar"))
            self.assertTrue(dst_fs.isfile("test.txt"))

    def test_copy_value_error(self):
        src_fs = open_fs("mem://")
        dst_fs = open_fs("mem://")
        with self.assertRaises(ValueError):
            fs.copy.copy_fs(src_fs, dst_fs, workers=-1)

    def test_copy_dir(self):
        src_fs = open_fs("mem://")
        src_fs.makedirs("foo/bar")
        src_fs.makedirs("foo/empty")
        src_fs.touch("test.txt")
        src_fs.touch("foo/bar/baz.txt")
        for workers in (0, 1, 2, 4):
            with open_fs("mem://") as dst_fs:
                fs.copy.copy_dir(src_fs, "/foo", dst_fs, "/", workers=workers)
                self.assertTrue(dst_fs.isdir("bar"))
                self.assertTrue(dst_fs.isdir("empty"))
                self.assertTrue(dst_fs.isfile("bar/baz.txt"))

    def test_copy_large(self):
        data1 = b"foo" * 512 * 1024
        data2 = b"bar" * 2 * 512 * 1024
        data3 = b"baz" * 3 * 512 * 1024
        data4 = b"egg" * 7 * 512 * 1024
        with open_fs("temp://") as src_fs:
            src_fs.writebytes("foo", data1)
            src_fs.writebytes("bar", data2)
            src_fs.makedir("dir1").writebytes("baz", data3)
            src_fs.makedirs("dir2/dir3").writebytes("egg", data4)
            for workers in (0, 1, 2, 4):
                with open_fs("temp://") as dst_fs:
                    fs.copy.copy_fs(src_fs, dst_fs, workers=workers)
                    self.assertEqual(dst_fs.readbytes("foo"), data1)
                    self.assertEqual(dst_fs.readbytes("bar"), data2)
                    self.assertEqual(dst_fs.readbytes("dir1/baz"), data3)
                    self.assertEqual(dst_fs.readbytes("dir2/dir3/egg"), data4)

    def test_copy_dir_on_copy(self):
        src_fs = open_fs("mem://")
        src_fs.touch("baz.txt")

        on_copy_calls = []

        def on_copy(*args):
            on_copy_calls.append(args)

        dst_fs = open_fs("mem://")
        fs.copy.copy_dir(src_fs, "/", dst_fs, "/", on_copy=on_copy)
        self.assertEqual(on_copy_calls, [(src_fs, "/baz.txt", dst_fs, "/baz.txt")])

    def mkdirp(self, path):
        # os.makedirs(path, exist_ok=True) only for python3.?
        try:
            os.makedirs(path)
        except OSError as exc:
            if exc.errno == errno.EEXIST and os.path.isdir(path):
                pass
            else:
                raise

    def _create_sandbox_dir(self, prefix="pyfilesystem2_sandbox_", home=None):
        if home is None:
            return tempfile.mkdtemp(prefix=prefix)
        else:
            sandbox_path = os.path.join(home, prefix)
            self.mkdirp(sandbox_path)
            return sandbox_path

    def _touch(self, root, filepath):
        # create abs filename
        abs_filepath = os.path.join(root, filepath)
        # create dir
        dirname = os.path.dirname(abs_filepath)
        self.mkdirp(dirname)
        # touch file
        with open(abs_filepath, "a"):
            os.utime(
                abs_filepath, None
            )  # update the mtime in case the file exists, same as touch

        return abs_filepath

    def _write_file(self, filepath, write_chars=1024):
        with open(filepath, "w") as f:
            f.write("1" * write_chars)
        return filepath

    def _delay_file_utime(self, filepath, delta_sec):
        utcnow = datetime.datetime.utcnow()
        unix_timestamp = calendar.timegm(utcnow.timetuple())
        times = unix_timestamp + delta_sec, unix_timestamp + delta_sec
        os.utime(filepath, times)

    def test_copy_file_if_newer_same_fs(self):
        src_fs = open_fs("mem://")
        src_fs.makedir("foo2").touch("exists")
        src_fs.makedir("foo1").touch("test1.txt")
        src_fs.settimes(
            "foo2/exists", datetime.datetime.utcnow() + datetime.timedelta(hours=1)
        )
        self.assertTrue(
            fs.copy.copy_file_if_newer(
                src_fs, "foo1/test1.txt", src_fs, "foo2/test1.txt.copy"
            )
        )
        self.assertFalse(
            fs.copy.copy_file_if_newer(src_fs, "foo1/test1.txt", src_fs, "foo2/exists")
        )
        self.assertTrue(src_fs.exists("foo2/test1.txt.copy"))

    def test_copy_file_if_newer_dst_older(self):
        try:
            # create first dst ==> dst is older the src ==> file should be copied
            dst_dir = self._create_sandbox_dir()
            dst_file1 = self._touch(dst_dir, "file1.txt")
            self._write_file(dst_file1)

            src_dir = self._create_sandbox_dir()
            src_file1 = self._touch(src_dir, "file1.txt")
            self._write_file(src_file1)
            # ensure src file is newer than dst, changing its modification time
            self._delay_file_utime(src_file1, delta_sec=60)

            src_fs = open_fs("osfs://" + src_dir)
            dst_fs = open_fs("osfs://" + dst_dir)

            self.assertTrue(dst_fs.exists("/file1.txt"))

            copied = fs.copy.copy_file_if_newer(
                src_fs, "/file1.txt", dst_fs, "/file1.txt"
            )

            self.assertTrue(copied)
            self.assertTrue(dst_fs.exists("/file1.txt"))
        finally:
            shutil.rmtree(src_dir)
            shutil.rmtree(dst_dir)

    def test_copy_file_if_newer_dst_doesnt_exists(self):
        try:
            src_dir = self._create_sandbox_dir()
            src_file1 = self._touch(src_dir, "file1.txt")
            self._write_file(src_file1)

            dst_dir = self._create_sandbox_dir()

            src_fs = open_fs("osfs://" + src_dir)
            dst_fs = open_fs("osfs://" + dst_dir)

            copied = fs.copy.copy_file_if_newer(
                src_fs, "/file1.txt", dst_fs, "/file1.txt"
            )

            self.assertTrue(copied)
            self.assertTrue(dst_fs.exists("/file1.txt"))
        finally:
            shutil.rmtree(src_dir)
            shutil.rmtree(dst_dir)

    def test_copy_file_if_newer_dst_is_newer(self):
        try:
            src_dir = self._create_sandbox_dir()
            src_file1 = self._touch(src_dir, "file1.txt")
            self._write_file(src_file1)

            dst_dir = self._create_sandbox_dir()
            dst_file1 = self._touch(dst_dir, "file1.txt")
            self._write_file(dst_file1)

            src_fs = open_fs("osfs://" + src_dir)
            dst_fs = open_fs("osfs://" + dst_dir)

            self.assertTrue(dst_fs.exists("/file1.txt"))

            copied = fs.copy.copy_file_if_newer(
                src_fs, "/file1.txt", dst_fs, "/file1.txt"
            )

            self.assertEqual(copied, False)
        finally:
            shutil.rmtree(src_dir)
            shutil.rmtree(dst_dir)

    def test_copy_fs_if_newer_dst_older(self):
        try:
            # create first dst ==> dst is older the src ==> file should be copied
            dst_dir = self._create_sandbox_dir()
            dst_file1 = self._touch(dst_dir, "file1.txt")
            self._write_file(dst_file1)

            src_dir = self._create_sandbox_dir()
            src_file1 = self._touch(src_dir, "file1.txt")
            self._write_file(src_file1)
            # ensure src file is newer than dst, changing its modification time
            self._delay_file_utime(src_file1, delta_sec=60)

            src_fs = open_fs("osfs://" + src_dir)
            dst_fs = open_fs("osfs://" + dst_dir)

            self.assertTrue(dst_fs.exists("/file1.txt"))

            copied = []

            def on_copy(src_fs, src_path, dst_fs, dst_path):
                copied.append(dst_path)

            fs.copy.copy_fs_if_newer(src_fs, dst_fs, on_copy=on_copy)

            self.assertEqual(copied, ["/file1.txt"])
            self.assertTrue(dst_fs.exists("/file1.txt"))

            src_fs.close()
            dst_fs.close()

        finally:
            shutil.rmtree(src_dir)
            shutil.rmtree(dst_dir)

    def test_copy_fs_if_newer_when_dst_doesnt_exists(self):
        try:
            src_dir = self._create_sandbox_dir()
            src_file1 = self._touch(src_dir, "file1.txt")
            self._write_file(src_file1)

            src_file2 = self._touch(src_dir, "one_level_down" + os.sep + "file2.txt")
            self._write_file(src_file2)

            dst_dir = self._create_sandbox_dir()

            src_fs = open_fs("osfs://" + src_dir)
            dst_fs = open_fs("osfs://" + dst_dir)

            copied = []

            def on_copy(src_fs, src_path, dst_fs, dst_path):
                copied.append(dst_path)

            fs.copy.copy_fs_if_newer(src_fs, dst_fs, on_copy=on_copy)

            self.assertEqual(copied, ["/file1.txt", "/one_level_down/file2.txt"])
            self.assertTrue(dst_fs.exists("/file1.txt"))
            self.assertTrue(dst_fs.exists("/one_level_down/file2.txt"))

            src_fs.close()
            dst_fs.close()

        finally:
            shutil.rmtree(src_dir)
            shutil.rmtree(dst_dir)

    def test_copy_fs_if_newer_dont_copy_when_dst_exists(self):
        try:
            # src is older than dst => no copy should be necessary
            src_dir = self._create_sandbox_dir()
            src_file1 = self._touch(src_dir, "file1.txt")
            self._write_file(src_file1)

            dst_dir = self._create_sandbox_dir()
            dst_file1 = self._touch(dst_dir, "file1.txt")
            self._write_file(dst_file1)
            # ensure dst file is newer than src, changing its modification time
            self._delay_file_utime(dst_file1, delta_sec=60)

            src_fs = open_fs("osfs://" + src_dir)
            dst_fs = open_fs("osfs://" + dst_dir)

            self.assertTrue(dst_fs.exists("/file1.txt"))

            copied = []

            def on_copy(src_fs, src_path, dst_fs, dst_path):
                copied.append(dst_path)

            fs.copy.copy_fs_if_newer(src_fs, dst_fs, on_copy=on_copy)

            self.assertEqual(copied, [])
            self.assertTrue(dst_fs.exists("/file1.txt"))

            src_fs.close()
            dst_fs.close()

        finally:
            shutil.rmtree(src_dir)
            shutil.rmtree(dst_dir)

    def test_copy_dir_if_newer_one_dst_doesnt_exist(self):
        try:

            src_dir = self._create_sandbox_dir()
            src_file1 = self._touch(src_dir, "file1.txt")
            self._write_file(src_file1)

            src_file2 = self._touch(src_dir, "one_level_down" + os.sep + "file2.txt")
            self._write_file(src_file2)

            dst_dir = self._create_sandbox_dir()
            dst_file1 = self._touch(dst_dir, "file1.txt")
            self._write_file(dst_file1)
            # ensure dst file is newer than src, changing its modification time
            self._delay_file_utime(dst_file1, delta_sec=60)

            src_fs = open_fs("osfs://" + src_dir)
            dst_fs = open_fs("osfs://" + dst_dir)

            copied = []

            def on_copy(src_fs, src_path, dst_fs, dst_path):
                copied.append(dst_path)

            fs.copy.copy_dir_if_newer(src_fs, "/", dst_fs, "/", on_copy=on_copy)

            self.assertEqual(copied, ["/one_level_down/file2.txt"])
            self.assertTrue(dst_fs.exists("/one_level_down/file2.txt"))

            src_fs.close()
            dst_fs.close()
        finally:
            shutil.rmtree(src_dir)
            shutil.rmtree(dst_dir)

    def test_copy_dir_if_newer_same_fs(self):
        try:
            src_dir = self._create_sandbox_dir()
            src_file1 = self._touch(src_dir, "src" + os.sep + "file1.txt")
            self._write_file(src_file1)

            self._create_sandbox_dir(home=src_dir)

            src_fs = open_fs("osfs://" + src_dir)

            copied = []

            def on_copy(src_fs, src_path, dst_fs, dst_path):
                copied.append(dst_path)

            fs.copy.copy_dir_if_newer(src_fs, "/src", src_fs, "/dst", on_copy=on_copy)

            self.assertEqual(copied, ["/dst/file1.txt"])
            self.assertTrue(src_fs.exists("/dst/file1.txt"))

            src_fs.close()

        finally:
            shutil.rmtree(src_dir)

    def test_copy_dir_if_newer_multiple_files(self):
        try:
            src_dir = self._create_sandbox_dir()
            src_fs = open_fs("osfs://" + src_dir)
            src_fs.makedirs("foo/bar")
            src_fs.makedirs("foo/empty")
            src_fs.touch("test.txt")
            src_fs.touch("foo/bar/baz.txt")

            dst_dir = self._create_sandbox_dir()
            dst_fs = open_fs("osfs://" + dst_dir)

            fs.copy.copy_dir_if_newer(src_fs, "/foo", dst_fs, "/")

            self.assertTrue(dst_fs.isdir("bar"))
            self.assertTrue(dst_fs.isdir("empty"))
            self.assertTrue(dst_fs.isfile("bar/baz.txt"))
        finally:
            shutil.rmtree(src_dir)
            shutil.rmtree(dst_dir)


if __name__ == "__main__":
    unittest.main()
