from __future__ import unicode_literals

import unittest

from fs.mode import validate_open_mode
from fs.mode import validate_openbin_mode
from fs import tools
from fs.opener import open_fs


class TestTools(unittest.TestCase):
    def test_remove_empty(self):
        fs = open_fs("temp://")
        fs.makedirs("foo/bar/baz/egg/")
        fs.create("foo/bar/test.txt")

        tools.remove_empty(fs, "foo/bar/baz/egg")
        self.assertFalse(fs.isdir("foo/bar/baz"))
        self.assertTrue(fs.isdir("foo/bar"))
        fs.remove("foo/bar/test.txt")

        tools.remove_empty(fs, "foo/bar")
        self.assertEqual(fs.listdir("/"), [])

    def test_validate_openbin_mode(self):
        with self.assertRaises(ValueError):
            validate_openbin_mode("X")
        with self.assertRaises(ValueError):
            validate_openbin_mode("")
        with self.assertRaises(ValueError):
            validate_openbin_mode("rX")
        with self.assertRaises(ValueError):
            validate_openbin_mode("rt")
        validate_openbin_mode("r")
        validate_openbin_mode("w")
        validate_openbin_mode("a")
        validate_openbin_mode("r+")
        validate_openbin_mode("w+")
        validate_openbin_mode("a+")

    def test_validate_open_mode(self):
        with self.assertRaises(ValueError):
            validate_open_mode("X")
        with self.assertRaises(ValueError):
            validate_open_mode("")
        with self.assertRaises(ValueError):
            validate_open_mode("rX")

        validate_open_mode("rt")
        validate_open_mode("r")
        validate_open_mode("rb")
        validate_open_mode("w")
        validate_open_mode("a")
        validate_open_mode("r+")
        validate_open_mode("w+")
        validate_open_mode("a+")
