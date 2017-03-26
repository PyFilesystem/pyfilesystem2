from __future__ import unicode_literals

import os
import tempfile
import unittest
import zipfile

from fs import zipfs
from fs.compress import write_zip
from fs.opener import open_fs
from fs.test import FSTestCases

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


class TestReadZipFSMem(TestReadZipFS):

    def make_source_fs(self):
        return open_fs('mem://')


class TestDirsZipFS(unittest.TestCase):

    def test_implied(self):
        """Test zipfs creates intermediate directories."""
        fh, path = tempfile.mkstemp('testzip.zip')
        try:
            os.close(fh)
            _zip_file = zipfile.ZipFile(path, mode='w')
            _zip_file.writestr('foo/bar/baz/egg', b'hello')
            _zip_file.close()
            zip_fs = zipfs.ZipFS(path)
            zip_fs.getinfo('foo')
            zip_fs.getinfo('foo/bar')
            zip_fs.getinfo('foo/bar/baz')
            self.assertTrue(zip_fs.isdir('foo/bar/baz'))
            self.assertTrue(zip_fs.isfile('foo/bar/baz/egg'))
        finally:
            os.remove(path)


