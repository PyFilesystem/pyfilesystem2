from __future__ import unicode_literals

import os
import six
import gzip
import tempfile
import unittest

from fs import tarfs
from fs.compress import write_tar
from fs.opener import open_fs
from fs.test import FSTestCases

from .test_archives import ArchiveTestCases


class TestWriteTarFS(FSTestCases, unittest.TestCase):
    """
    Test TarFS implementation.

    When writing, a ZipFS is essentially a TempFS.

    """

    def make_fs(self):
        _tar_file = tempfile.TemporaryFile()
        fs = tarfs.TarFS(_tar_file, write=True)
        fs._tar_file = _tar_file
        return fs

    def destroy_fs(self, fs):
        fs.close()
        del fs._tar_file

class TestWriteGZippedTarFS(FSTestCases, unittest.TestCase):

    def make_fs(self):
        _tar_file = tempfile.TemporaryFile()
        fs = tarfs.TarFS(_tar_file, write=True, compression="gz")
        fs._tar_file = _tar_file
        return fs

    def destroy_fs(self, fs):
        fs.close()
        del fs._tar_file

    def assert_is_bzip(self):
        try:
            tarfile.open(fs._tar_file, 'r:gz')
        except tarfile.ReadError:
            self.fail("{} is not a valid gz archive".format(fs._tar_file))
        for other_comps in ['xz', 'bz2', '']:
            with self.assertRaises(tarfile.ReadError):
                tarfile.open(fs._tar_file,
                             'r:{}'.format(other_comps))

@unittest.skipIf(six.PY2, "Python2 does not support LZMA")
class TestWriteXZippedTarFS(FSTestCases, unittest.TestCase):

    def make_fs(self):
        _tar_file = tempfile.TemporaryFile()
        fs = tarfs.TarFS(_tar_file, write=True, compression="xz")
        fs._tar_file = _tar_file
        return fs

    def destroy_fs(self, fs):
        fs.close()
        del fs._tar_file

    def assert_is_xz(self):
        try:
            tarfile.open(fs._tar_file, 'r:xz')
        except tarfile.ReadError:
            self.fail("{} is not a valid xz archive".format(fs._tar_file))
        for other_comps in ['bz2', 'gz', '']:
            with self.assertRaises(tarfile.ReadError):
                tarfile.open(fs._tar_file,
                             'r:{}'.format(other_comps))

class TestWriteBZippedTarFS(FSTestCases, unittest.TestCase):

    def make_fs(self):
        _tar_file = tempfile.TemporaryFile()
        fs = tarfs.TarFS(_tar_file, write=True, compression="gz")
        fs._tar_file = _tar_file
        return fs

    def destroy_fs(self, fs):
        fs.close()
        del fs._tar_file

    def assert_is_bzip(self):
        try:
            tarfile.open(fs._tar_file, 'r:bz2')
        except tarfile.ReadError:
            self.fail("{} is not a valid bz2 archive".format(fs._tar_file))
        for other_comps in ['xz', 'gz', '']:
            with self.assertRaises(tarfile.ReadError):
                tarfile.open(fs._tar_file,
                             'r:{}'.format(other_comps))

class TestReadTarFS(ArchiveTestCases, unittest.TestCase):
    """
    Test Reading tar files.

    """
    def compress(self, fs):
        fh, self._temp_path = tempfile.mkstemp()
        os.close(fh)
        write_tar(fs, self._temp_path)

    def load_archive(self):
        return tarfs.TarFS(self._temp_path)

    def remove_archive(self):
        os.remove(self._temp_path)

class TestReadTarFSMem(TestReadTarFS):

    def make_source_fs(self):
        return open_fs('mem://')