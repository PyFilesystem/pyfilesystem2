from __future__ import unicode_literals

import errno
import unittest
from unittest import mock

import fs.errors
from fs import error_tools
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

    def test_convert_eacces_sharing_violation_on_windows(self):
        # On Windows, EACCES with winerror 32 (ERROR_SHARING_VIOLATION)
        # means the file is locked by another process, not a plain
        # permissions problem.
        exception = OSError(errno.EACCES, "file in use")
        exception.winerror = 32
        with mock.patch.object(error_tools.sys, "platform", "win32"):
            with self.assertRaises(fs.errors.ResourceLocked) as ctx:
                with convert_os_errors("open", "/tmp/test"):
                    raise exception
        self.assertEqual(ctx.exception.exc, exception)
        self.assertEqual(ctx.exception.path, "/tmp/test")

    def test_convert_eacces_plain_permission_denied_on_windows(self):
        # A plain EACCES without the sharing-violation winerror should
        # still be reported as PermissionDenied.
        exception = OSError(errno.EACCES, "denied")
        with mock.patch.object(error_tools.sys, "platform", "win32"):
            with self.assertRaises(fs.errors.PermissionDenied) as ctx:
                with convert_os_errors("open", "/tmp/test"):
                    raise exception
        self.assertEqual(ctx.exception.exc, exception)
        self.assertEqual(ctx.exception.path, "/tmp/test")
