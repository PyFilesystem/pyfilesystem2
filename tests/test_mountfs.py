from __future__ import unicode_literals

import unittest

from fs.mountfs import MountError, MountFS
from fs.memoryfs import MemoryFS
from fs.tempfs import TempFS
from fs.test import FSTestCases


class TestMountFS(FSTestCases, unittest.TestCase):
    """Test OSFS implementation."""

    def make_fs(self):
        fs = MountFS()
        mem_fs = MemoryFS()
        fs.mount('/', mem_fs)
        return fs


class TestMountFSBehaviours(unittest.TestCase):

    def test_listdir(self):
        mount_fs = MountFS()
        self.assertEqual(mount_fs.listdir('/'), [])
        m1 = MemoryFS()
        m2 = TempFS()
        m3 = MemoryFS()
        m4 = TempFS()
        mount_fs.mount('/m1', m1)
        mount_fs.mount('/m2', m2)
        mount_fs.mount('/m3', m3)
        with self.assertRaises(MountError):
            mount_fs.mount('/m3/foo', m4)
        self.assertEqual(
            sorted(mount_fs.listdir('/')),
            ['m1', 'm2', 'm3']
        )
        m3.makedir('foo')
        self.assertEqual(
            sorted(mount_fs.listdir('/m3')),
            ['foo']
        )

    def test_auto_close(self):
        """Test MountFS auto close is working"""
        mount_fs = MountFS()
        m1 = MemoryFS()
        m2 = MemoryFS()
        mount_fs.mount('/m1', m1)
        mount_fs.mount('/m2', m2)
        self.assertFalse(m1.isclosed())
        self.assertFalse(m2.isclosed())
        mount_fs.close()
        self.assertTrue(m1.isclosed())
        self.assertTrue(m2.isclosed())

    def test_no_auto_close(self):
        """Test MountFS auto close can be disabled"""
        mount_fs = MountFS(auto_close=False)
        m1 = MemoryFS()
        m2 = MemoryFS()
        mount_fs.mount('/m1', m1)
        mount_fs.mount('/m2', m2)
        self.assertFalse(m1.isclosed())
        self.assertFalse(m2.isclosed())
        mount_fs.close()
        self.assertFalse(m1.isclosed())
        self.assertFalse(m2.isclosed())

    def test_empty(self):
        """Test MountFS with nothing mounted."""
        mount_fs = MountFS()
        self.assertEqual(mount_fs.listdir('/'), [])

    def test_mount_self(self):
        mount_fs = MountFS()
        with self.assertRaises(ValueError):
            mount_fs.mount('/', mount_fs)

    def test_desc(self):
        mount_fs = MountFS()
        mount_fs.desc('/')
