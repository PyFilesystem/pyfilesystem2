# coding: utf-8
"""Test (abstract) base FS class."""

from __future__ import unicode_literals

import unittest
import platform

try:
    import mock
except ImportError:
    from unittest import mock


from fs.base import FS
from fs import errors


class TestFS(FS):
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
        self.fs = TestFS()

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

    def test_quote(self):
        test_fixtures = [
            # test_snippet, expected
            ["foo/bar/egg/foofoo", "foo/bar/egg/foofoo"],
            ["foo/bar ha/barz", "foo/bar%20ha/barz"],
            ["example b.txt", "example%20b.txt"],
            ["exampleㄓ.txt", "example%E3%84%93.txt"],
        ]
        if platform.system() == "Windows":
            test_fixtures.extend(
                [
                    ["C:\\My Documents\\test.txt", "C:/My%20Documents/test.txt"],
                    ["C:/My Documents/test.txt", "C:/My%20Documents/test.txt"],
                    # on Windows '\' is regarded as path separator
                    ["test/forward\\slash", "test/forward/slash"],
                ]
            )
        else:
            test_fixtures.extend(
                [
                    # colon:tmp is bad path under Windows
                    ["test/colon:tmp", "test/colon%3Atmp"],
                    # Unix treat \ as %5C
                    ["test/forward\\slash", "test/forward%5Cslash"],
                ]
            )
        for test_snippet, expected in test_fixtures:
            self.assertEqual(FS.quote(test_snippet), expected)
