from __future__ import unicode_literals

import errno
import sys
import unittest

import fs.errors
from fs.error_tools import convert_os_errors


class TestErrorTools(unittest.TestCase):
    def test_convert_enoent(self):
        exception = OSError(errno.ENOENT, "resource not found")
        with self.assertRaises(fs.errors.ResourceNotFound) as ctx:
            with convert_os_errors("stat", "/tmp/test"):
                raise exception
        self.assertEqual(ctx.exception.exc, exception)
        self.assertEqual(ctx.exception.path, "/tmp/test")

    def test_convert_enametoolong(self):
        exception = OSError(errno.ENAMETOOLONG, "File name too long: test")
        with self.assertRaises(fs.errors.PathError) as ctx:
            with convert_os_errors("stat", "/tmp/test"):
                raise exception
        self.assertEqual(ctx.exception.exc, exception)
        self.assertEqual(ctx.exception.path, "/tmp/test")

    @unittest.skipIf(sys.platform != "win32", "requires Windows")
    def test_convert_resourcelocked_windows(self):
        exception = OSError(32, "resource locked")
        with self.assertRaises(fs.errors.ResourceLocked) as ctx:
            with convert_os_errors("stat", "/tmp/test"):
                raise exception

        self.assertEqual(ctx.exception.exc, exception)
        self.assertEqual(ctx.exception.path, "/tmp/test")
