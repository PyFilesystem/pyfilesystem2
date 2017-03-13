from __future__ import unicode_literals

import io
import os
import mock
import shutil
import tempfile
import unittest

from fs import osfs
from fs.path import relpath
from fs import errors

from fs.test import FSTestCases


from six import text_type


class TestOSFS(FSTestCases, unittest.TestCase):
    """Test OSFS implementation."""

    def make_fs(self):
        temp_dir = tempfile.mkdtemp(u"fstestosfs")
        return osfs.OSFS(temp_dir)

    def destroy_fs(self, fs):
        self.fs.close()

    def _get_real_path(self, path):
        _path = os.path.join(self.fs.root_path, relpath(path))
        return _path

    def assert_exists(self, path):
        _path = self._get_real_path(path)
        self.assertTrue(os.path.exists(_path))

    def assert_not_exists(self, path):
        _path = self._get_real_path(path)
        self.assertFalse(os.path.exists(_path))

    def assert_isfile(self, path):
        _path = self._get_real_path(path)
        self.assertTrue(os.path.isfile(_path))

    def assert_isdir(self, path):
        _path = self._get_real_path(path)
        self.assertTrue(os.path.isdir(_path))

    def assert_bytes(self, path, contents):
        assert isinstance(contents, bytes)
        _path = self._get_real_path(path)
        with io.open(_path, 'rb') as f:
            data = f.read()
        self.assertEqual(data, contents)
        self.assertIsInstance(data, bytes)

    def assert_text(self, path, contents):
        assert isinstance(contents, text_type)
        _path = self._get_real_path(path)
        with io.open(_path, 'rt', encoding='utf-8') as f:
            data = f.read()
        self.assertEqual(data, contents)
        self.assertIsInstance(data, text_type)

    def test_not_exists(self):
        with self.assertRaises(errors.CreateFailed):
            fs = osfs.OSFS('/does/not/exists/')

    def test_create(self):
        """Test create=True"""

        dir_path = tempfile.mkdtemp()
        try:
            create_dir = os.path.join(dir_path, 'test_create')
            with osfs.OSFS(create_dir, create=True):
                self.assertTrue(os.path.isdir(create_dir))
            self.assertTrue(os.path.isdir(create_dir))
        finally:
            shutil.rmtree(dir_path)

        # Test exception when unable to create dir
        with tempfile.NamedTemporaryFile() as tmp_file:
            with self.assertRaises(errors.CreateFailed):
                # Trying to create a dir that exists as a file
                osfs.OSFS(tmp_file.name, create=True)

    def test_unicode_paths(self):
        dir_path = tempfile.mkdtemp()
        try:
            fs_dir = os.path.join(dir_path, u'te\u0161t_\u00fanicod\u0113')
            os.mkdir(fs_dir)
            with osfs.OSFS(fs_dir):
                self.assertTrue(os.path.isdir(fs_dir))
        finally:
            shutil.rmtree(dir_path)
