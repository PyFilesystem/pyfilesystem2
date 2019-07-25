from __future__ import unicode_literals

import os
import shutil
import tempfile
import unittest

from fs import osfs
from fs.subfs import SubFS
from fs.memoryfs import MemoryFS
from fs.path import relpath
from .test_osfs import TestOSFS


class TestSubFS(TestOSFS):
    """Test OSFS implementation."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp("fstest")
        self.parent_fs = osfs.OSFS(self.temp_dir)
        self.parent_fs.makedir("__subdir__")
        self.fs = self.parent_fs.opendir("__subdir__")

    def tearDown(self):
        shutil.rmtree(self.temp_dir)
        self.parent_fs.close()
        self.fs.close()

    def _get_real_path(self, path):
        _path = os.path.join(self.temp_dir, "__subdir__", relpath(path))
        return _path

class CustomSubFS(SubFS):
    """Just a custom class to change the type"""

class CustomSubFS2(SubFS):
    """Just a custom class to change the type"""

class CustomFS(MemoryFS):
    subfs_class = CustomSubFS

class TestCustomSubFS(unittest.TestCase):
    """Test customization of the SubFS returned from opendir etc"""

    def test_opendir(self):
        fs = CustomFS()
        fs.makedir("__subdir__")
        subfs = fs.opendir("__subdir__")
        # By default, you get the fs's defined custom SubFS
        assert isinstance(subfs, CustomSubFS)

        # Providing the factory explicitly still works
        subfs = fs.opendir("__subdir__", factory=CustomSubFS2)
        assert isinstance(subfs, CustomSubFS2)
