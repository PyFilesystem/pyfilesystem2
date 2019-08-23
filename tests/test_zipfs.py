# -*- encoding: UTF-8
from __future__ import unicode_literals

import os
import sys
import tempfile
import unittest
import zipfile

import six

from fs import zipfs
from fs.compress import write_zip
from fs.opener import open_fs
from fs.opener.errors import NotWriteable
from fs.errors import NoURL
from fs.test import FSTestCases
from fs.enums import Seek

from .test_archives import ArchiveTestCases


class TestWriteReadZipFS(unittest.TestCase):
    def setUp(self):
        fh, self._temp_path = tempfile.mkstemp()
        os.close(fh)

    def tearDown(self):
        os.remove(self._temp_path)

    def test_unicode_paths(self):
        # https://github.com/PyFilesystem/pyfilesystem2/issues/135
        with zipfs.ZipFS(self._temp_path, write=True) as zip_fs:
            zip_fs.writetext("Файл", "some content")

        with zipfs.ZipFS(self._temp_path) as zip_fs:
            paths = list(zip_fs.walk.files())
            for path in paths:
                self.assertIsInstance(path, six.text_type)
                with zip_fs.openbin(path) as f:
                    f.read()


class TestWriteZipFS(FSTestCases, unittest.TestCase):
    """
    Test ZIPFS implementation.

    When writing, a ZipFS is essentially a TempFS.

    """

    def make_fs(self):
        _zip_file = tempfile.TemporaryFile()
        fs = zipfs.ZipFS(_zip_file, write=True)
        fs._zip_file = _zip_file
        return fs

    def destroy_fs(self, fs):
        fs.close()
        del fs._zip_file


class TestReadZipFS(ArchiveTestCases, unittest.TestCase):
    """
    Test Reading zip files.

    """

    def compress(self, fs):
        fh, self._temp_path = tempfile.mkstemp()
        os.close(fh)
        write_zip(fs, self._temp_path)

    def load_archive(self):
        return zipfs.ZipFS(self._temp_path)

    def remove_archive(self):
        os.remove(self._temp_path)

    def test_large(self):
        test_fs = open_fs("mem://")
        test_fs.writebytes("test.bin", b"a" * 50000)
        write_zip(test_fs, self._temp_path)

        self.fs = self.load_archive()

        with self.fs.openbin("test.bin") as f:
            self.assertEqual(f.read(), b"a" * 50000)
        with self.fs.openbin("test.bin") as f:
            self.assertEqual(f.read(50000), b"a" * 50000)
        with self.fs.openbin("test.bin") as f:
            self.assertEqual(f.read1(), b"a" * 50000)
        with self.fs.openbin("test.bin") as f:
            self.assertEqual(f.read1(50000), b"a" * 50000)

    def test_getinfo(self):
        super(TestReadZipFS, self).test_getinfo()
        top = self.fs.getinfo("top.txt", ["zip"])
        if sys.platform in ("linux", "darwin"):
            self.assertEqual(top.get("zip", "create_system"), 3)

    def test_openbin(self):
        with self.fs.openbin("top.txt") as f:
            self.assertEqual(f.name, "top.txt")
        with self.fs.openbin("top.txt") as f:
            self.assertRaises(ValueError, f.seek, -2, Seek.set)
        with self.fs.openbin("top.txt") as f:
            self.assertRaises(ValueError, f.seek, 2, Seek.end)
        with self.fs.openbin("top.txt") as f:
            self.assertRaises(ValueError, f.seek, 0, 5)

    def test_read(self):
        with self.fs.openbin("top.txt") as f:
            self.assertEqual(f.read(), b"Hello, World")
        with self.fs.openbin("top.txt") as f:
            self.assertEqual(f.read(5), b"Hello")
            self.assertEqual(f.read(7), b", World")
        with self.fs.openbin("top.txt") as f:
            self.assertEqual(f.read(12), b"Hello, World")

    def test_read1(self):
        with self.fs.openbin("top.txt") as f:
            self.assertEqual(f.read1(), b"Hello, World")
        with self.fs.openbin("top.txt") as f:
            self.assertEqual(f.read1(5), b"Hello")
            self.assertEqual(f.read1(7), b", World")
        with self.fs.openbin("top.txt") as f:
            self.assertEqual(f.read1(12), b"Hello, World")

    def test_seek_set(self):
        with self.fs.openbin("top.txt") as f:
            self.assertEqual(f.tell(), 0)
            self.assertEqual(f.read(), b"Hello, World")
            self.assertEqual(f.tell(), 12)
            self.assertEqual(f.read(), b"")
            self.assertEqual(f.tell(), 12)
            self.assertEqual(f.seek(0), 0)
            self.assertEqual(f.tell(), 0)
            self.assertEqual(f.read1(), b"Hello, World")
            self.assertEqual(f.tell(), 12)
            self.assertEqual(f.seek(1), 1)
            self.assertEqual(f.tell(), 1)
            self.assertEqual(f.read(), b"ello, World")
            self.assertEqual(f.tell(), 12)
            self.assertEqual(f.seek(7), 7)
            self.assertEqual(f.tell(), 7)
            self.assertEqual(f.read(), b"World")
            self.assertEqual(f.tell(), 12)

    def test_seek_current(self):
        with self.fs.openbin("top.txt") as f:
            self.assertEqual(f.tell(), 0)
            self.assertEqual(f.read(5), b"Hello")
            self.assertEqual(f.tell(), 5)
            self.assertEqual(f.seek(2, Seek.current), 7)
            self.assertEqual(f.read1(), b"World")
            self.assertEqual(f.tell(), 12)
            self.assertEqual(f.seek(-1, Seek.current), 11)
            self.assertEqual(f.read(), b"d")
        with self.fs.openbin("top.txt") as f:
            self.assertRaises(ValueError, f.seek, -1, Seek.current)

    def test_seek_end(self):
        with self.fs.openbin("top.txt") as f:
            self.assertEqual(f.tell(), 0)
            self.assertEqual(f.seek(-12, Seek.end), 0)
            self.assertEqual(f.read1(5), b"Hello")
            self.assertEqual(f.seek(-7, Seek.end), 5)
            self.assertEqual(f.seek(-5, Seek.end), 7)
            self.assertEqual(f.read(), b"World")

    def test_geturl_for_fs(self):
        test_file = "foo/bar/egg/foofoo"
        expected = "zip://{zip_file_path}!/{file_inside_zip}".format(
            zip_file_path=self._temp_path.replace("\\", "/"), file_inside_zip=test_file
        )
        self.assertEqual(self.fs.geturl(test_file, purpose="fs"), expected)

    def test_geturl_for_fs_but_file_is_binaryio(self):
        self.fs._file = six.BytesIO()
        self.assertRaises(NoURL, self.fs.geturl, "test", "fs")

    def test_geturl_for_download(self):
        test_file = "foo/bar/egg/foofoo"
        with self.assertRaises(NoURL):
            self.fs.geturl(test_file)

    def test_read_non_existent_file(self):
        fs = zipfs.ZipFS(open(self._temp_path, "rb"))
        # it has been very difficult to catch exception in __del__()
        del fs._zip
        try:
            fs.close()
        except AttributeError:
            self.fail("Could not close tar fs properly")
        except Exception:
            self.fail("Strange exception in closing fs")


class TestReadZipFSMem(TestReadZipFS):
    def make_source_fs(self):
        return open_fs("mem://")


class TestDirsZipFS(unittest.TestCase):
    def test_implied(self):
        """Test zipfs creates intermediate directories."""
        fh, path = tempfile.mkstemp("testzip.zip")
        try:
            os.close(fh)
            with zipfile.ZipFile(path, mode="w") as z:
                z.writestr("foo/bar/baz/egg", b"hello")
            with zipfs.ReadZipFS(path) as zip_fs:
                foo = zip_fs.getinfo("foo", ["details"])
                self.assertEqual(zip_fs.getinfo("foo/bar").name, "bar")
                self.assertEqual(zip_fs.getinfo("foo/bar/baz").name, "baz")
                self.assertTrue(foo.is_dir)
                self.assertTrue(zip_fs.isfile("foo/bar/baz/egg"))
        finally:
            os.remove(path)


class TestOpener(unittest.TestCase):
    def test_not_writeable(self):
        with self.assertRaises(NotWriteable):
            open_fs("zip://foo.zip", writeable=True)
