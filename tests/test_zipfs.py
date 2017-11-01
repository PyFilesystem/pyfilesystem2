from __future__ import unicode_literals

import os
import sys
import tempfile
import unittest
import zipfile

from fs import zipfs
from fs.compress import write_zip
from fs.opener import open_fs
from fs.opener.errors import NotWriteable
from fs.test import FSTestCases
from fs.enums import Seek, ResourceType

from .test_archives import ArchiveTestCases


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

    def test_getinfo(self):
        super(TestReadZipFS, self).test_getinfo()
        top = self.fs.getinfo('top.txt', ['zip'])
        if sys.platform in ('linux', 'darwin'):
            self.assertEqual(top.get('zip', 'create_system'), 3)

    def test_openbin(self):
        with self.fs.openbin('top.txt') as f:
            self.assertEqual(f.name, 'top.txt')
        with self.fs.openbin('top.txt') as f:
            self.assertRaises(ValueError, f.seek, -2, Seek.set)
        with self.fs.openbin('top.txt') as f:
            self.assertRaises(ValueError, f.seek, 2, Seek.end)
        with self.fs.openbin('top.txt') as f:
            self.assertRaises(ValueError, f.seek, 0, 5)

    def test_read(self):
        with self.fs.openbin('top.txt') as f:
            self.assertEqual(f.read(), b'Hello, World')
        with self.fs.openbin('top.txt') as f:
            self.assertEqual(f.read(5), b'Hello')
            self.assertEqual(f.read(7), b', World')
        with self.fs.openbin('top.txt') as f:
            self.assertEqual(f.read(12), b'Hello, World')

    def test_read1(self):
        with self.fs.openbin('top.txt') as f:
            self.assertEqual(f.read1(), b'Hello, World')
        with self.fs.openbin('top.txt') as f:
            self.assertEqual(f.read1(5), b'Hello')
            self.assertEqual(f.read1(7), b', World')
        with self.fs.openbin('top.txt') as f:
            self.assertEqual(f.read1(12), b'Hello, World')

    def test_seek_set(self):
        with self.fs.openbin('top.txt') as f:
            self.assertEqual(f.tell(), 0)
            self.assertEqual(f.read(), b'Hello, World')
            self.assertEqual(f.tell(), 12)
            self.assertEqual(f.read(), b'')
            self.assertEqual(f.tell(), 12)
            self.assertEqual(f.seek(0), 0)
            self.assertEqual(f.tell(), 0)
            self.assertEqual(f.read1(), b'Hello, World')
            self.assertEqual(f.tell(), 12)
            self.assertEqual(f.seek(1), 1)
            self.assertEqual(f.tell(), 1)
            self.assertEqual(f.read(), b'ello, World')
            self.assertEqual(f.tell(), 12)
            self.assertEqual(f.seek(7), 7)
            self.assertEqual(f.tell(), 7)
            self.assertEqual(f.read(), b'World')
            self.assertEqual(f.tell(), 12)

    def test_seek_current(self):
        with self.fs.openbin('top.txt') as f:
            self.assertEqual(f.tell(), 0)
            self.assertEqual(f.read(5), b'Hello')
            self.assertEqual(f.tell(), 5)
            self.assertEqual(f.seek(2, Seek.current), 7)
            self.assertEqual(f.read1(), b'World')
            self.assertEqual(f.tell(), 12)
            self.assertEqual(f.seek(-1, Seek.current), 11)
            self.assertEqual(f.read(), b'd')
        with self.fs.openbin('top.txt') as f:
            self.assertRaises(ValueError, f.seek, -1, Seek.current)

    def test_seek_end(self):
        with self.fs.openbin('top.txt') as f:
            self.assertEqual(f.tell(), 0)
            self.assertEqual(f.seek(-12, Seek.end), 0)
            self.assertEqual(f.read1(5), b'Hello')
            self.assertEqual(f.seek(-7, Seek.end), 5)
            self.assertEqual(f.seek(-5, Seek.end), 7)
            self.assertEqual(f.read(), b'World')


class TestReadZipFSMem(TestReadZipFS):

    def make_source_fs(self):
        return open_fs('mem://')


class TestDirsZipFS(unittest.TestCase):

    def test_implied(self):
        """Test zipfs creates intermediate directories."""
        fh, path = tempfile.mkstemp('testzip.zip')
        try:
            os.close(fh)
            with zipfile.ZipFile(path, mode='w') as z:
                z.writestr('foo/bar/baz/egg', b'hello')
            with zipfs.ReadZipFS(path) as zip_fs:
                foo = zip_fs.getinfo('foo', ['details'])
                bar = zip_fs.getinfo('foo/bar')
                baz = zip_fs.getinfo('foo/bar/baz')
                self.assertTrue(foo.is_dir)
                self.assertTrue(zip_fs.isfile('foo/bar/baz/egg'))
        finally:
            os.remove(path)


class TestOpener(unittest.TestCase):

    def test_not_writeable(self):
        with self.assertRaises(NotWriteable):
            open_fs('zip://foo.zip', writeable=True)
