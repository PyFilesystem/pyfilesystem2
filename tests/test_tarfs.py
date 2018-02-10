# -*- encoding: UTF-8
from __future__ import unicode_literals

import os
import six
import gzip
import tarfile
import getpass
import tempfile
import unittest

from fs import tarfs
from fs import errors
from fs.compress import write_tar
from fs.opener import open_fs
from fs.opener.errors import NotWriteable
from fs.test import FSTestCases

from .test_archives import ArchiveTestCases


class TestWriteReadTarFS(unittest.TestCase):

    def setUp(self):
        fh, self._temp_path = tempfile.mkstemp()

    def tearDown(self):
        os.remove(self._temp_path)

    def test_unicode_paths(self):
        # https://github.com/PyFilesystem/pyfilesystem2/issues/135
        with tarfs.TarFS(self._temp_path, write=True) as tar_fs:
            tar_fs.settext("Файл", "some content")

        with tarfs.TarFS(self._temp_path) as tar_fs:
            paths = list(tar_fs.walk.files())
            for path in paths:
                self.assertIsInstance(path, six.text_type)
                with tar_fs.openbin(path) as f:
                    f.read()


class TestWriteTarFS(FSTestCases, unittest.TestCase):
    """
    Test TarFS implementation.

    When writing, a TarFS is essentially a TempFS.
    """

    def make_fs(self):
        fh, _tar_file = tempfile.mkstemp()
        os.close(fh)
        fs = tarfs.TarFS(_tar_file, write=True)
        fs._tar_file = _tar_file
        return fs

    def destroy_fs(self, fs):
        fs.close()
        del fs._tar_file

class TestWriteTarFSToFileobj(FSTestCases, unittest.TestCase):
    """
    Test TarFS implementation.

    When writing, a TarFS is essentially a TempFS.

    """

    def make_fs(self):
        _tar_file = six.BytesIO()
        fs = tarfs.TarFS(_tar_file, write=True)
        fs._tar_file = _tar_file
        return fs

    def destroy_fs(self, fs):
        fs.close()
        del fs._tar_file

class TestWriteGZippedTarFS(FSTestCases, unittest.TestCase):

    def make_fs(self):
        fh, _tar_file = tempfile.mkstemp()
        os.close(fh)
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
        fh, _tar_file = tempfile.mkstemp()
        os.close(fh)
        fs = tarfs.TarFS(_tar_file, write=True, compression="xz")
        fs._tar_file = _tar_file
        return fs

    def destroy_fs(self, fs):
        fs.close()
        self.assert_is_xz(fs)
        os.remove(fs._tar_file)
        del fs._tar_file

    def assert_is_xz(self, fs):
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
        fh, _tar_file = tempfile.mkstemp()
        os.close(fh)
        fs = tarfs.TarFS(_tar_file, write=True, compression="bz2")
        fs._tar_file = _tar_file
        return fs

    def destroy_fs(self, fs):
        fs.close()
        self.assert_is_bzip(fs)
        os.remove(fs._tar_file)
        del fs._tar_file

    def assert_is_bzip(self, fs):
        try:
            tarfile.open(fs._tar_file, 'r:bz2')
        except tarfile.ReadError:
            self.fail("{} is not a valid bz2 archive".format(fs._tar_file))
        for other_comps in ['gz', '']:
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

    def test_read_from_fileobject(self):
        try:
            tarfs.TarFS(open(self._temp_path, 'rb'))
        except:
            self.fail("Couldn't open tarfs from fileobject")

    def test_read_from_filename(self):
        try:
            tarfs.TarFS(self._temp_path)
        except:
            self.fail("Couldn't open tarfs from filename")

    def test_getinfo(self):
        super(TestReadTarFS, self).test_getinfo()
        top = self.fs.getinfo('top.txt', ['tar'])
        self.assertTrue(top.get('tar', 'is_file'))


class TestReadTarFSMem(TestReadTarFS):

    def make_source_fs(self):
        return open_fs('mem://')


class TestOpener(unittest.TestCase):

    def test_not_writeable(self):
        with self.assertRaises(NotWriteable):
            open_fs('tar://foo.zip', writeable=True)
