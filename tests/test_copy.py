from __future__ import unicode_literals

import os
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


    def _create_dir(self, prefix='pyfilesystem2_tests_'):
        return tempfile.mkdtemp(prefix=prefix)

    def _create_file(self, filename, write_chars=1024):
        dir = self._create_dir()
        fn = os.path.join(dir, filename)
        if write_chars > 0:
            with open(fn, 'w') as f:
                f.write('1' * write_chars)
        return dir, fn

    def test_copy_when_dst_doesnt_exist(self):
        try:

            filename = "file1.txt"
            src_dir, _ = self._create_file(filename, 1024)
            dst_dir, _ = self._create_file(filename, 0)

            src_fs = open_fs('osfs://' + src_dir)
            dst_fs = open_fs('osfs://' + dst_dir)

            copied = fs.copy.copy_fs(src_fs, dst_fs, copy_if_newer=True)

            self.assertEqual(copied, ["/" + filename])
            self.assertTrue(dst_fs.exists(filename))

            src_fs.close()
            dst_fs.close()

        finally:
            shutil.rmtree(src_dir)
            shutil.rmtree(dst_dir)

    def test_dont_copy_when_dst_exists(self):
        try:

            filename = "file1.txt"
            src_dir, _ = self._create_file(filename, 1024)
            dst_dir, _ = self._create_file(filename, 1024)

            src_fs = open_fs('osfs://' + src_dir)
            dst_fs = open_fs('osfs://' + dst_dir)

            self.assertTrue(dst_fs.exists(filename))

            copied = fs.copy.copy_fs(src_fs, dst_fs, copy_if_newer=True)

            self.assertEqual(copied, [])
            self.assertTrue(dst_fs.exists(filename))

            src_fs.close()
            dst_fs.close()

        finally:
            shutil.rmtree(src_dir)
            shutil.rmtree(dst_dir)

    def test_copy_when_src_is_newer(self):
        try:

            filename = "file1.txt"
            #create first dst ==> dst is older the src
            dst_dir, _ = self._create_file(filename, 1024)
            src_dir, _ = self._create_file(filename, 1024)

            src_fs = open_fs('osfs://' + src_dir)
            dst_fs = open_fs('osfs://' + dst_dir)

            self.assertTrue(dst_fs.exists(filename))

            copied = fs.copy.copy_fs(src_fs, dst_fs, copy_if_newer=True)

            self.assertEqual(copied, ["/" + filename])
            self.assertTrue(dst_fs.exists(filename))

            src_fs.close()
            dst_fs.close()

        finally:
            shutil.rmtree(src_dir)
            shutil.rmtree(dst_dir)

