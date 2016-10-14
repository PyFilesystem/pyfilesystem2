from __future__ import unicode_literals

import unittest

from fs import wrapfs
from fs.opener import open_fs


class TestWrapFS(unittest.TestCase):

    def setUp(self):
        self.wrapped_fs = open_fs('mem://')
        self.fs = wrapfs.WrapFS(self.wrapped_fs)

    def test_encode(self):
        self.assertEqual((self.wrapped_fs, 'foo'), self.fs.delegate_path('foo'))
        self.assertEqual((self.wrapped_fs, 'bar'), self.fs.delegate_path('bar'))
        self.assertIs(self.wrapped_fs, self.fs.delegate_fs())
