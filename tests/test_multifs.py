from __future__ import unicode_literals

import unittest

from fs.multifs import MultiFS
from fs.memoryfs import MemoryFS
from fs import errors

from fs.test import FSTestCases


class TestMultiFS(FSTestCases, unittest.TestCase):
    """Test OSFS implementation."""

    def setUp(self):
        fs = MultiFS()
        mem_fs = MemoryFS()
        fs.add_fs('mem', mem_fs, write=True)
        self.fs = fs
        self.mem_fs = mem_fs

    def make_fs(self):
        fs = MultiFS()
        mem_fs = MemoryFS()
        fs.add_fs('mem', mem_fs, write=True)
        return fs

    def test_get_fs(self):
        self.assertIs(self.fs.get_fs('mem'), self.mem_fs)

    def test_which(self):
        self.fs.setbytes('foo', b'bar')
        self.assertEqual(self.fs.which('foo'), ('mem', self.mem_fs))
        self.assertEqual(self.fs.which('bar', 'w'), ('mem', self.mem_fs))
        self.assertEqual(self.fs.which('baz'), (None, None))

    def test_auto_close(self):
        """Test MultiFS auto close is working"""
        multi_fs = MultiFS()
        m1 = MemoryFS()
        m2 = MemoryFS()
        multi_fs.add_fs('m1', m1)
        multi_fs.add_fs('m2', m2)
        self.assertFalse(m1.isclosed())
        self.assertFalse(m2.isclosed())
        multi_fs.close()
        self.assertTrue(m1.isclosed())
        self.assertTrue(m2.isclosed())

    def test_no_auto_close(self):
        """Test MultiFS auto close can be disabled"""
        multi_fs = MultiFS(auto_close=False)
        self.assertEqual(
            repr(multi_fs),
            "MultiFS(auto_close=False)"
        )
        m1 = MemoryFS()
        m2 = MemoryFS()
        multi_fs.add_fs('m1', m1)
        multi_fs.add_fs('m2', m2)
        self.assertFalse(m1.isclosed())
        self.assertFalse(m2.isclosed())
        multi_fs.close()
        self.assertFalse(m1.isclosed())
        self.assertFalse(m2.isclosed())

    def test_priority(self):
        """Test priority order is working"""
        m1 = MemoryFS()
        m2 = MemoryFS()
        m3 = MemoryFS()
        m1.setbytes("name", b"m1")
        m2.setbytes("name", b"m2")
        m3.setbytes("name", b"m3")
        multi_fs = MultiFS(auto_close=False)
        multi_fs.add_fs("m1", m1)
        multi_fs.add_fs("m2", m2)
        multi_fs.add_fs("m3", m3)
        self.assertEqual(multi_fs.getbytes("name"), b"m3")

        m1 = MemoryFS()
        m2 = MemoryFS()
        m3 = MemoryFS()
        m1.setbytes("name", b"m1")
        m2.setbytes("name", b"m2")
        m3.setbytes("name", b"m3")
        multi_fs = MultiFS(auto_close=False)
        multi_fs.add_fs("m1", m1)
        multi_fs.add_fs("m2", m2, priority=10)
        multi_fs.add_fs("m3", m3)
        self.assertEqual(multi_fs.getbytes("name"), b"m2")

        m1 = MemoryFS()
        m2 = MemoryFS()
        m3 = MemoryFS()
        m1.setbytes("name", b"m1")
        m2.setbytes("name", b"m2")
        m3.setbytes("name", b"m3")
        multi_fs = MultiFS(auto_close=False)
        multi_fs.add_fs("m1", m1)
        multi_fs.add_fs("m2", m2, priority=10)
        multi_fs.add_fs("m3", m3, priority=10)
        self.assertEqual(multi_fs.getbytes("name"), b"m3")

        m1 = MemoryFS()
        m2 = MemoryFS()
        m3 = MemoryFS()
        m1.setbytes("name", b"m1")
        m2.setbytes("name", b"m2")
        m3.setbytes("name", b"m3")
        multi_fs = MultiFS(auto_close=False)
        multi_fs.add_fs("m1", m1, priority=11)
        multi_fs.add_fs("m2", m2, priority=10)
        multi_fs.add_fs("m3", m3, priority=10)
        self.assertEqual(multi_fs.getbytes("name"), b"m1")

    def test_no_writable(self):
        fs = MultiFS()
        with self.assertRaises(errors.ResourceReadOnly):
            fs.setbytes('foo', b'bar')

    def test_validate_path(self):
        self.fs.write_fs = None
        self.fs.validatepath('foo')
