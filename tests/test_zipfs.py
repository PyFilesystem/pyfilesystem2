from __future__ import unicode_literals

import os
import tempfile
import unittest

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
