from __future__ import unicode_literals

import unittest

from fs import errors
from fs.memoryfs import MemoryFS
from fs.multifs import MultiFS
from fs.test import FSTestCases


class TestMultiFS(FSTestCases, unittest.TestCase):
    """Test OSFS implementation."""

    def setUp(self):
        fs = MultiFS()
        mem_fs = MemoryFS()
        fs.add_fs("mem", mem_fs, write=True)
        self.fs = fs
        self.mem_fs = mem_fs

    def make_fs(self):
        fs = MultiFS()
        mem_fs = MemoryFS()
        fs.add_fs("mem", mem_fs, write=True)
        return fs

    def test_get_fs(self):
        self.assertIs(self.fs.get_fs("mem"), self.mem_fs)

    def test_which(self):
        self.fs.writebytes("foo", b"bar")
        self.assertEqual(self.fs.which("foo"), ("mem", self.mem_fs))
        self.assertEqual(self.fs.which("bar", "w"), ("mem", self.mem_fs))
        self.assertEqual(self.fs.which("baz"), (None, None))

    def test_auto_close(self):
        """Test MultiFS auto close is working"""
        multi_fs = MultiFS()
        m1 = MemoryFS()
        m2 = MemoryFS()
        multi_fs.add_fs("m1", m1)
        multi_fs.add_fs("m2", m2)
        self.assertFalse(m1.isclosed())
        self.assertFalse(m2.isclosed())
        multi_fs.close()
        self.assertTrue(m1.isclosed())
        self.assertTrue(m2.isclosed())

    def test_no_auto_close(self):
        """Test MultiFS auto close can be disabled"""
        multi_fs = MultiFS(auto_close=False)
        self.assertEqual(repr(multi_fs), "MultiFS(auto_close=False)")
        m1 = MemoryFS()
        m2 = MemoryFS()
        multi_fs.add_fs("m1", m1)
        multi_fs.add_fs("m2", m2)
        self.assertFalse(m1.isclosed())
        self.assertFalse(m2.isclosed())
        multi_fs.close()
        self.assertFalse(m1.isclosed())
        self.assertFalse(m2.isclosed())

    def test_opener(self):
        """Test use of FS URLs."""
        multi_fs = MultiFS()
        with self.assertRaises(TypeError):
            multi_fs.add_fs("foo", 5)
        multi_fs.add_fs("f1", "mem://")
        multi_fs.add_fs("f2", "temp://")
        self.assertIsInstance(multi_fs.get_fs("f1"), MemoryFS)

    def test_priority(self):
        """Test priority order is working"""
        m1 = MemoryFS()
        m2 = MemoryFS()
        m3 = MemoryFS()
        m1.writebytes("name", b"m1")
        m2.writebytes("name", b"m2")
        m3.writebytes("name", b"m3")
        multi_fs = MultiFS(auto_close=False)
        multi_fs.add_fs("m1", m1)
        multi_fs.add_fs("m2", m2)
        multi_fs.add_fs("m3", m3)
        self.assertEqual(multi_fs.readbytes("name"), b"m3")

        m1 = MemoryFS()
        m2 = MemoryFS()
        m3 = MemoryFS()
        m1.writebytes("name", b"m1")
        m2.writebytes("name", b"m2")
        m3.writebytes("name", b"m3")
        multi_fs = MultiFS(auto_close=False)
        multi_fs.add_fs("m1", m1)
        multi_fs.add_fs("m2", m2, priority=10)
        multi_fs.add_fs("m3", m3)
        self.assertEqual(multi_fs.readbytes("name"), b"m2")

        m1 = MemoryFS()
        m2 = MemoryFS()
        m3 = MemoryFS()
        m1.writebytes("name", b"m1")
        m2.writebytes("name", b"m2")
        m3.writebytes("name", b"m3")
        multi_fs = MultiFS(auto_close=False)
        multi_fs.add_fs("m1", m1)
        multi_fs.add_fs("m2", m2, priority=10)
        multi_fs.add_fs("m3", m3, priority=10)
        self.assertEqual(multi_fs.readbytes("name"), b"m3")

        m1 = MemoryFS()
        m2 = MemoryFS()
        m3 = MemoryFS()
        m1.writebytes("name", b"m1")
        m2.writebytes("name", b"m2")
        m3.writebytes("name", b"m3")
        multi_fs = MultiFS(auto_close=False)
        multi_fs.add_fs("m1", m1, priority=11)
        multi_fs.add_fs("m2", m2, priority=10)
        multi_fs.add_fs("m3", m3, priority=10)
        self.assertEqual(multi_fs.readbytes("name"), b"m1")

    def test_remove_requires_writable_filesystem(self):
        with MultiFS() as fs:
            readonly = MemoryFS()
            readonly.writebytes("file", b"keep")
            fs.add_fs("readonly", readonly)
            with self.assertRaises(errors.ResourceReadOnly):
                fs.remove("file")
            self.assertEqual(readonly.readbytes("file"), b"keep")

    def test_removedir_requires_writable_filesystem(self):
        with MultiFS() as fs:
            readonly = MemoryFS()
            readonly.makedir("directory")
            fs.add_fs("readonly", readonly)
            with self.assertRaises(errors.ResourceReadOnly):
                fs.removedir("directory")
            self.assertTrue(readonly.isdir("directory"))

    def test_remove_uses_writable_filesystem(self):
        readonly = MemoryFS()
        readonly.writebytes("file", b"keep")
        self.mem_fs.writebytes("file", b"remove")
        self.fs.add_fs("readonly", readonly, priority=1)
        self.fs.remove("file")
        self.assertFalse(self.mem_fs.exists("file"))
        self.assertEqual(readonly.readbytes("file"), b"keep")

    def test_removedir_uses_writable_filesystem(self):
        readonly = MemoryFS()
        readonly.makedir("directory")
        self.mem_fs.makedir("directory")
        self.fs.add_fs("readonly", readonly, priority=1)
        self.fs.removedir("directory")
        self.assertFalse(self.mem_fs.exists("directory"))
        self.assertTrue(readonly.isdir("directory"))

    def test_remove_does_not_fall_back_to_readonly_filesystem(self):
        readonly = MemoryFS()
        readonly.writebytes("file", b"keep")
        self.fs.add_fs("readonly", readonly)
        with self.assertRaises(errors.ResourceNotFound):
            self.fs.remove("file")
        self.assertEqual(readonly.readbytes("file"), b"keep")

    def test_removedir_does_not_fall_back_to_readonly_filesystem(self):
        readonly = MemoryFS()
        readonly.makedir("directory")
        self.fs.add_fs("readonly", readonly)
        with self.assertRaises(errors.ResourceNotFound):
            self.fs.removedir("directory")
        self.assertTrue(readonly.isdir("directory"))

    def test_no_writable(self):
        fs = MultiFS()
        with self.assertRaises(errors.ResourceReadOnly):
            fs.writebytes("foo", b"bar")

    def test_validate_path(self):
        self.fs.write_fs = None
        self.fs.validatepath("foo")

    def test_listdir_duplicates(self):
        m1 = MemoryFS()
        m2 = MemoryFS()
        m1.touch("foo")
        m2.touch("foo")
        multi_fs = MultiFS()
        multi_fs.add_fs("m1", m1)
        multi_fs.add_fs("m2", m2)
        self.assertEqual(multi_fs.listdir("/"), ["foo"])
