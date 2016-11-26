from __future__ import unicode_literals

import os
import shutil
import tempfile

from fs import osfs
from fs.path import relpath
from .test_osfs import TestOSFS


class TestSubFS(TestOSFS):
    """Test OSFS implementation."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp("fstest")
        self.parent_fs = osfs.OSFS(self.temp_dir)
        self.parent_fs.makedir('__subdir__')
        self.fs = self.parent_fs.opendir('__subdir__')

    def tearDown(self):
        shutil.rmtree(self.temp_dir)
        self.parent_fs.close()
        self.fs.close()

    def _get_real_path(self, path):
        _path = os.path.join(self.temp_dir, '__subdir__', relpath(path))
        return _path
