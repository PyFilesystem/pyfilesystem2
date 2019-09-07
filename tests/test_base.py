"""Test (abstract) base FS class."""

from __future__ import unicode_literals

import unittest

from fs.base import FS
from fs import errors


class DummyFS(FS):
    def getinfo(self, path, namespaces=None):
        pass

    def listdir(self, path):
        pass

    def makedir(self, path, permissions=None, recreate=False):
        pass

    def openbin(self, path, mode="r", buffering=-1, **options):
        pass

    def remove(self, path):
        pass

    def removedir(self, path):
        pass

    def setinfo(self, path, info):
        pass


class TestBase(unittest.TestCase):
    def setUp(self):
        self.fs = DummyFS()

    def test_validatepath(self):
        """Test validatepath method."""
        with self.assertRaises(TypeError):
            self.fs.validatepath(b"bytes")

        self.fs._meta["invalid_path_chars"] = "Z"
        with self.assertRaises(errors.InvalidCharsInPath):
            self.fs.validatepath("Time for some ZZZs")

        self.fs.validatepath("fine")
        self.fs.validatepath("good.fine")

        self.fs._meta["invalid_path_chars"] = ""
        self.fs.validatepath("Time for some ZZZs")

        def mock_getsyspath(path):
            return path

        self.fs.getsyspath = mock_getsyspath

        self.fs._meta["max_sys_path_length"] = 10

        self.fs.validatepath("0123456789")
        self.fs.validatepath("012345678")
        self.fs.validatepath("01234567")

        with self.assertRaises(errors.InvalidPath):
            self.fs.validatepath("0123456789A")
