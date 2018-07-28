from __future__ import unicode_literals

import unittest

from six import text_type

from fs import wrapfs
from fs.opener import open_fs


class WrappedFS(wrapfs.WrapFS):
    wrap_name = "test"


class TestWrapFS(unittest.TestCase):
    def setUp(self):
        self.wrapped_fs = open_fs("mem://")
        self.fs = WrappedFS(self.wrapped_fs)

    def test_encode(self):
        self.assertEqual((self.wrapped_fs, "foo"), self.fs.delegate_path("foo"))
        self.assertEqual((self.wrapped_fs, "bar"), self.fs.delegate_path("bar"))
        self.assertIs(self.wrapped_fs, self.fs.delegate_fs())

    def test_repr(self):
        self.assertEqual(repr(self.fs), "WrappedFS(MemoryFS())")

    def test_str(self):
        self.assertEqual(text_type(self.fs), "<memfs>(test)")
        self.assertEqual(text_type(wrapfs.WrapFS(open_fs("mem://"))), "<memfs>")
