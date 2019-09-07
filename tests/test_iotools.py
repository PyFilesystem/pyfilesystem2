from __future__ import unicode_literals

import io
import unittest

import six

from fs import iotools
from fs import tempfs

from fs.test import UNICODE_TEXT


class TestIOTools(unittest.TestCase):
    def setUp(self):
        self.fs = tempfs.TempFS("iotoolstest")

    def tearDown(self):
        self.fs.close()
        del self.fs

    def test_make_stream(self):
        """Test make_stream"""

        self.fs.writebytes("foo.bin", b"foofoo")

        with self.fs.openbin("foo.bin") as f:
            data = f.read()
            self.assertTrue(isinstance(data, bytes))

        with self.fs.openbin("text.txt", "wb") as f:
            f.write(UNICODE_TEXT.encode("utf-8"))

        with self.fs.openbin("text.txt") as f:
            with iotools.make_stream("text.txt", f, "rt") as f2:
                repr(f2)
                text = f2.read()
                self.assertIsInstance(text, six.text_type)

    def test_readinto(self):

        self.fs.writebytes("bytes.bin", b"foofoobarbar")

        with self.fs.openbin("bytes.bin") as bin_file:
            with iotools.make_stream("bytes.bin", bin_file, "rb") as f:
                data = bytearray(3)
                bytes_read = f.readinto(data)
                self.assertEqual(bytes_read, 3)
                self.assertEqual(bytes(data), b"foo")
                self.assertEqual(f.readline(1), b"f")

        def no_readinto(size):
            raise AttributeError

        with self.fs.openbin("bytes.bin") as bin_file:
            bin_file.readinto = no_readinto
            with iotools.make_stream("bytes.bin", bin_file, "rb") as f:
                data = bytearray(3)
                bytes_read = f.readinto(data)
                self.assertEqual(bytes_read, 3)
                self.assertEqual(bytes(data), b"foo")
                self.assertEqual(f.readline(1), b"f")

    def test_readinto1(self):

        self.fs.writebytes("bytes.bin", b"foofoobarbar")

        with self.fs.openbin("bytes.bin") as bin_file:
            with iotools.make_stream("bytes.bin", bin_file, "rb") as f:
                data = bytearray(3)
                bytes_read = f.readinto1(data)
                self.assertEqual(bytes_read, 3)
                self.assertEqual(bytes(data), b"foo")
                self.assertEqual(f.readline(1), b"f")

        def no_readinto(size):
            raise AttributeError

        with self.fs.openbin("bytes.bin") as bin_file:
            bin_file.readinto = no_readinto
            with iotools.make_stream("bytes.bin", bin_file, "rb") as f:
                data = bytearray(3)
                bytes_read = f.readinto1(data)
                self.assertEqual(bytes_read, 3)
                self.assertEqual(bytes(data), b"foo")
                self.assertEqual(f.readline(1), b"f")

    def test_isatty(self):
        with self.fs.openbin("text.txt", "wb") as f:
            with iotools.make_stream("text.txt", f, "wb") as f1:
                self.assertFalse(f1.isatty())

    def test_readlines(self):
        self.fs.writebytes("foo", b"barbar\nline1\nline2")
        with self.fs.open("foo", "rb") as f:
            f = iotools.make_stream("foo", f, "rb")
            self.assertEqual(list(f), [b"barbar\n", b"line1\n", b"line2"])
        with self.fs.open("foo", "rt") as f:
            f = iotools.make_stream("foo", f, "rb")
            self.assertEqual(f.readlines(), ["barbar\n", "line1\n", "line2"])

    def test_readall(self):
        self.fs.writebytes("foo", b"foobar")
        with self.fs.open("foo", "rt") as f:
            self.assertEqual(f.read(), "foobar")

    def test_writelines(self):
        with self.fs.open("foo", "wb") as f:
            f = iotools.make_stream("foo", f, "rb")
            f.writelines([b"foo", b"bar", b"baz"])
        self.assertEqual(self.fs.readbytes("foo"), b"foobarbaz")

    def test_seekable(self):

        f = io.BytesIO(b"HelloWorld")
        raw_wrapper = iotools.RawWrapper(f)
        self.assertTrue(raw_wrapper.seekable())

        def no_seekable():
            raise AttributeError("seekable")

        f.seekable = no_seekable

        def seek(pos, whence):
            raise IOError("no seek")

        raw_wrapper.seek = seek

        self.assertFalse(raw_wrapper.seekable())

    def test_line_iterator(self):
        f = io.BytesIO(b"Hello\nWorld\n\nfoo")
        self.assertEqual(
            list(iotools.line_iterator(f)), [b"Hello\n", b"World\n", b"\n", b"foo"]
        )

        f = io.BytesIO(b"Hello\nWorld\n\nfoo")
        self.assertEqual(list(iotools.line_iterator(f, 10)), [b"Hello\n", b"Worl"])

    def test_make_stream_writer(self):
        f = io.BytesIO()
        s = iotools.make_stream("foo", f, "wb", buffering=1)
        self.assertIsInstance(s, io.BufferedWriter)
        s.write(b"Hello")
        self.assertEqual(f.getvalue(), b"Hello")

    def test_make_stream_reader(self):
        f = io.BytesIO(b"Hello")
        s = iotools.make_stream("foo", f, "rb", buffering=1)
        self.assertIsInstance(s, io.BufferedReader)
        self.assertEqual(s.read(), b"Hello")

    def test_make_stream_reader_writer(self):
        f = io.BytesIO(b"Hello")
        s = iotools.make_stream("foo", f, "+b", buffering=1)
        self.assertIsInstance(s, io.BufferedRandom)
        self.assertEqual(s.read(), b"Hello")
        s.write(b" World")
        self.assertEqual(f.getvalue(), b"Hello World")
