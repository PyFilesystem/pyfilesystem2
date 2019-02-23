from __future__ import unicode_literals

import os
import platform
import shutil
import tempfile
import unittest

import six

import fs
from fs.osfs import OSFS


if platform.system() != "Windows":

    @unittest.skipIf(platform.system() == "Darwin", "Bad unicode not possible on OSX")
    class TestEncoding(unittest.TestCase):

        TEST_FILENAME = b"foo\xb1bar"
        # fsdecode throws error on Windows
        TEST_FILENAME_UNICODE = fs.fsdecode(TEST_FILENAME)

        def setUp(self):
            dir_path = self.dir_path = tempfile.mkdtemp()
            if six.PY2:
                with open(os.path.join(dir_path, self.TEST_FILENAME), "wb") as f:
                    f.write(b"baz")
            else:
                with open(
                    os.path.join(dir_path, self.TEST_FILENAME_UNICODE), "wb"
                ) as f:
                    f.write(b"baz")

        def tearDown(self):
            shutil.rmtree(self.dir_path)

        def test_open(self):
            with OSFS(self.dir_path) as test_fs:
                self.assertTrue(test_fs.exists(self.TEST_FILENAME_UNICODE))
                self.assertTrue(test_fs.isfile(self.TEST_FILENAME_UNICODE))
                self.assertFalse(test_fs.isdir(self.TEST_FILENAME_UNICODE))
                with test_fs.open(self.TEST_FILENAME_UNICODE, "rb") as f:
                    self.assertEqual(f.read(), b"baz")
                self.assertEqual(test_fs.readtext(self.TEST_FILENAME_UNICODE), "baz")
                test_fs.remove(self.TEST_FILENAME_UNICODE)
                self.assertFalse(test_fs.exists(self.TEST_FILENAME_UNICODE))

        def test_listdir(self):
            with OSFS(self.dir_path) as test_fs:
                dirlist = test_fs.listdir("/")
                self.assertEqual(dirlist, [self.TEST_FILENAME_UNICODE])
                self.assertEqual(test_fs.readtext(dirlist[0]), "baz")

        def test_scandir(self):
            with OSFS(self.dir_path) as test_fs:
                for info in test_fs.scandir("/"):
                    self.assertIsInstance(info.name, six.text_type)
                    self.assertEqual(info.name, self.TEST_FILENAME_UNICODE)
