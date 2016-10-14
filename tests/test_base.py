"""Test (abstract) base FS class."""

from __future__ import unicode_literals

import unittest

try:
    import mock
except ImportError:
    from unittest import mock


from fs.base import FS
from fs import errors


class TestBase(unittest.TestCase):
    def setUp(self):
        self.fs = FS()

    def test_validatepath(self):
        """Test validatepath method."""
        with self.assertRaises(ValueError):
            self.fs.validatepath(b'bytes')

        self.fs._meta['invalid_path_chars'] = 'Z'
        with self.assertRaises(errors.InvalidCharsInPath):
            self.fs.validatepath('Time for some ZZZs')

        self.fs.validatepath('fine')
        self.fs.validatepath('good.fine')

        self.fs._meta['invalid_path_chars'] = ''
        self.fs.validatepath('Time for some ZZZs')

        def mock_getsyspath(path):
            return path
        self.fs.getsyspath = mock_getsyspath

        self.fs._meta['max_sys_path_length'] = 10

        self.fs.validatepath('0123456789')
        self.fs.validatepath('012345678')
        self.fs.validatepath('01234567')

        with self.assertRaises(errors.InvalidPath):
            self.fs.validatepath('0123456789A')


class TestNotImplemented(unittest.TestCase):
    def setUp(self):
        self.fs = FS()

    def test_not_implemented(self):
        with self.assertRaises(NotImplementedError):
            self.fs.getinfo('foo')
        with self.assertRaises(NotImplementedError):
            self.fs.listdir('foo')
        with self.assertRaises(NotImplementedError):
            self.fs.makedir('foo')
        with self.assertRaises(NotImplementedError):
            self.fs.openbin('foo')
        with self.assertRaises(NotImplementedError):
            self.fs.remove('foo')
        with self.assertRaises(NotImplementedError):
            self.fs.removedir('foo')
