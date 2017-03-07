from __future__ import unicode_literals

import os
import time
import unittest
import tempfile
import shutil
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

    def _create_sandbox_dir(self, prefix='pyfilesystem2_sandbox_', home=None):
        if home is None:
            return tempfile.mkdtemp(prefix=prefix)
        else:
            sandbox_path = os.path.join(home, prefix)
            os.makedirs(sandbox_path, exist_ok=True)
            return sandbox_path

    def _touch(self, root, filepath):
        #create abs filename
        abs_filepath = os.path.join(root, filepath)
        #ensure dir exists, caution: exist_ok works only for python>=3.2
        #os.makedirs(os.path.dirname(abs_filepath), exist_ok=True)
        dirname = os.path.dirname(abs_filepath)
        try:
            os.makedirs(dirname)
        except OSError:
            if os.path.exists(dirname):
                pass
            else:
                raise
        #touch file
        with open(abs_filepath, 'a'):
            os.utime(abs_filepath, None) #update the mtime in case the file exists, same as touch
        return abs_filepath

    def _write_file(self, filepath, write_chars=1024):
        with open(filepath, 'w') as f:
            f.write('1' * write_chars)
        return filepath

    def test_copy_file_if_newer_dst_older(self):
        try:
            #create first dst ==> dst is older the src ==> file should be copied
            dst_dir = self._create_sandbox_dir()
            dst_file1 = self._touch(dst_dir, "file1.txt")
            self._write_file(dst_file1)

            src_dir = self._create_sandbox_dir()
            src_file1 = self._touch(src_dir, "file1.txt")
            self._write_file(src_file1)

            src_fs = open_fs('osfs://' + src_dir)
            dst_fs = open_fs('osfs://' + dst_dir)

            self.assertTrue(dst_fs.exists("/file1.txt"))

            copied = fs.copy.copy_file_if_newer(src_fs, "/file1.txt", dst_fs, "/file1.txt")

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

            src_fs = open_fs('osfs://' + src_dir)
            dst_fs = open_fs('osfs://' + dst_dir)


            copied = fs.copy.copy_file_if_newer(src_fs, "/file1.txt", dst_fs, "/file1.txt")

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

            src_fs = open_fs('osfs://' + src_dir)
            dst_fs = open_fs('osfs://' + dst_dir)


            self.assertTrue(dst_fs.exists("/file1.txt"))

            copied = fs.copy.copy_file_if_newer(src_fs, "/file1.txt", dst_fs, "/file1.txt")

            self.assertEqual(copied, False)
        finally:
            shutil.rmtree(src_dir)
            shutil.rmtree(dst_dir)


    def test_copy_fs_if_newer_dst_older(self):
        try:
            #create first dst ==> dst is older the src ==> file should be copied
            dst_dir = self._create_sandbox_dir()
            dst_file1 = self._touch(dst_dir, "file1.txt")
            self._write_file(dst_file1)

            src_dir = self._create_sandbox_dir()
            src_file1 = self._touch(src_dir, "file1.txt")
            self._write_file(src_file1)

            src_fs = open_fs('osfs://' + src_dir)
            dst_fs = open_fs('osfs://' + dst_dir)

            self.assertTrue(dst_fs.exists("/file1.txt"))

            copied = []
            def callback(src_fs, src_path, dst_fs, dst_path):
                copied.append(dst_path)

            fs.copy.copy_fs_if_newer(src_fs, dst_fs, callback=callback)

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

            src_fs = open_fs('osfs://' + src_dir)
            dst_fs = open_fs('osfs://' + dst_dir)

            copied = []
            def callback(src_fs, src_path, dst_fs, dst_path):
                copied.append(dst_path)

            fs.copy.copy_fs_if_newer(src_fs, dst_fs, callback=callback)

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
            #src is older than dst => no copy should be necessary
            src_dir = self._create_sandbox_dir()
            src_file1 = self._touch(src_dir, "file1.txt")
            self._write_file(src_file1)

            dst_dir = self._create_sandbox_dir()
            dst_file1 = self._touch(dst_dir, "file1.txt")
            self._write_file(dst_file1)

            src_fs = open_fs('osfs://' + src_dir)
            dst_fs = open_fs('osfs://' + dst_dir)

            self.assertTrue(dst_fs.exists("/file1.txt"))

            copied = []
            def callback(src_fs, src_path, dst_fs, dst_path):
                copied.append(dst_path)

            fs.copy.copy_fs_if_newer(src_fs, dst_fs, callback=callback)

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

            src_fs = open_fs('osfs://' + src_dir)
            dst_fs = open_fs('osfs://' + dst_dir)

            copied = []
            def callback(src_fs, src_path, dst_fs, dst_path):
                copied.append(dst_path)

            fs.copy.copy_dir_if_newer(src_fs, "/", dst_fs, "/", callback=callback)

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

            dst_dir = self._create_sandbox_dir(home=src_dir)

            src_fs = open_fs('osfs://' + src_dir)
            # dst_fs = open_fs('osfs://' + dst_dir)

            copied = []
            def callback(src_fs, src_path, dst_fs, dst_path):
                copied.append(dst_path)            

            fs.copy.copy_dir_if_newer(src_fs, "/src", src_fs, "/dst", callback=callback)

            self.assertEqual(copied, ["/dst/file1.txt"])
            self.assertTrue(src_fs.exists("/dst/file1.txt"))

            src_fs.close()

        finally:
            shutil.rmtree(src_dir)

    def test_copy_dir_if_newer_multiple_files(self):

        try:
            src_dir = self._create_sandbox_dir()
            src_fs = open_fs('osfs://' + src_dir)
            src_fs.makedirs('foo/bar')
            src_fs.makedirs('foo/empty')
            src_fs.touch('test.txt')
            src_fs.touch('foo/bar/baz.txt')

            dst_dir = self._create_sandbox_dir()
            dst_fs = open_fs('osfs://' + dst_dir)

            fs.copy.copy_dir_if_newer(src_fs, '/foo', dst_fs, '/')

            self.assertTrue(dst_fs.isdir('bar'))
            self.assertTrue(dst_fs.isdir('empty'))
            self.assertTrue(dst_fs.isfile('bar/baz.txt'))
        finally:
            shutil.rmtree(src_dir)
            shutil.rmtree(dst_dir)

if __name__ == "__main__":
    unittest.main()