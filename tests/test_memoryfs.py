from __future__ import unicode_literals

import unittest

from fs import memoryfs
from .test_fs import FSTestCases


class TestMemoryFS(FSTestCases, unittest.TestCase):
    """Test OSFS implementation."""

    def make_fs(self):
        return memoryfs.MemoryFS()
