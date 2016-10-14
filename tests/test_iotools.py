from __future__ import unicode_literals

import unittest

import six

from fs import iotools
from fs import tempfs

from .test_fs import UNICODE_TEXT


class TestIOTools(unittest.TestCase):

    def setUp(self):
        self.fs = tempfs.TempFS('iotoolstest')

    def tearDown(self):
        self.fs.close()
        del self.fs

    def test_make_stream(self):
        """Test make_stream"""

        self.fs.setbytes('foo.bin', b'foofoo')

        with self.fs.openbin('foo.bin') as f:
            data = f.read()
            self.assert_(isinstance(data, bytes))

        with self.fs.openbin('text.txt', 'wb') as f:
            f.write(UNICODE_TEXT.encode('utf-8'))

        with self.fs.openbin('text.txt') as f:
            with iotools.make_stream("text.txt", f, 'rt') as f2:
                repr(f2)
                text = f2.read()
                self.assertIsInstance(text, six.text_type)

    def test_readinto(self):

        self.fs.setbytes('bytes.bin', b'foofoobarbar')

        with self.fs.openbin('bytes.bin') as bin_file:
            with iotools.make_stream('bytes.bin', bin_file, 'rb') as f:
                data = bytearray(3)
                bytes_read = f.readinto(data)
                self.assertEqual(bytes_read, 3)
                self.assertEqual(bytes(data), b'foo')
                self.assertEqual(f.readline(1), b'f')
