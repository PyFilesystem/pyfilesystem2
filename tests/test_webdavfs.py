from __future__ import unicode_literals

import unittest

from fs import webdavfs
from fs.test import FSTestCases


class TestWebDAVFS(FSTestCases, unittest.TestCase):
    """Test WebDAVFS implementation."""

    def make_fs(self):
        url = 'https://api.dropbox.com/1/account/info'
        return webdavfs.WebDAVFS(url)
