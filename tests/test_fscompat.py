from __future__ import unicode_literals

import unittest

import six

from fs._fscompat import fsencode, fsdecode, fspath


class PathMock(object):
    def __init__(self, path):
        self._path = path

    def __fspath__(self):
        return self._path


class BrokenPathMock(object):
    def __init__(self, path):
        self._path = path

    def __fspath__(self):
        return self.broken


class TestFSCompact(unittest.TestCase):
    def test_fspath(self):
        path = PathMock("foo")
        self.assertEqual(fspath(path), "foo")
        path = PathMock(b"foo")
        self.assertEqual(fspath(path), b"foo")
        path = "foo"
        assert path is fspath(path)

        with self.assertRaises(TypeError):
            fspath(100)

        with self.assertRaises(TypeError):
            fspath(PathMock(5))

        with self.assertRaises(AttributeError):
            fspath(BrokenPathMock("foo"))

    def test_fsencode(self):
        encode_bytes = fsencode(b"foo")
        assert isinstance(encode_bytes, bytes)
        self.assertEqual(encode_bytes, b"foo")

        encode_bytes = fsencode("foo")
        assert isinstance(encode_bytes, bytes)
        self.assertEqual(encode_bytes, b"foo")

        with self.assertRaises(TypeError):
            fsencode(5)

    def test_fsdecode(self):
        decode_text = fsdecode(b"foo")
        assert isinstance(decode_text, six.text_type)
        decode_text = fsdecode("foo")
        assert isinstance(decode_text, six.text_type)
        with self.assertRaises(TypeError):
            fsdecode(5)
