from __future__ import unicode_literals

import unittest

from fs.errors import ResourceNotFound
from fs.mountfs import MountError, MountFS
from fs.memoryfs import MemoryFS
from fs.tempfs import TempFS
from fs.test import FSTestCases


class TestMountFS(FSTestCases, unittest.TestCase):
    """Test OSFS implementation."""

    def make_fs(self):
        fs = MountFS()
        mem_fs = MemoryFS()
        fs.mount("/foo", mem_fs)
        return fs.opendir("foo")


class TestMountFSBehaviours(unittest.TestCase):
    def test_bad_mount(self):
        mount_fs = MountFS()
        with self.assertRaises(TypeError):
            mount_fs.mount("foo", 5)
        with self.assertRaises(TypeError):
            mount_fs.mount("foo", b"bar")
        m1 = MemoryFS()
        with self.assertRaises(MountError):
            mount_fs.mount("", m1)
        with self.assertRaises(MountError):
            mount_fs.mount("/", m1)

    def test_listdir(self):
        mount_fs = MountFS()
        self.assertEqual(mount_fs.listdir("/"), [])
        m1 = MemoryFS()
        m3 = MemoryFS()
        m4 = TempFS()
        m5 = MemoryFS()
        mount_fs.mount("/m1", m1)
        mount_fs.mount("/m2", "temp://")
        mount_fs.mount("/m3", m3)
        with self.assertRaises(MountError):
            mount_fs.mount("/m3/foo", m4)
        self.assertEqual(sorted(mount_fs.listdir("/")), ["m1", "m2", "m3"])
        mount_fs.makedir("/m2/foo")
        self.assertEqual(sorted(mount_fs.listdir("/m2")), ["foo"])
        m3.makedir("foo")
        self.assertEqual(sorted(mount_fs.listdir("/m3")), ["foo"])
        mount_fs.mount("/subdir/m4", m4)
        self.assertEqual(sorted(mount_fs.listdir("/")), ["m1", "m2", "m3", "subdir"])
        self.assertEqual(mount_fs.listdir("/subdir"), ["m4"])
        self.assertEqual(mount_fs.listdir("/subdir/m4"), [])
        mount_fs.mount("/subdir/m5", m5)
        self.assertEqual(sorted(mount_fs.listdir("/subdir")), ["m4", "m5"])
        self.assertEqual(mount_fs.listdir("/subdir/m5"), [])
        mount_fs.makedir("/subdir/m4/foo")
        mount_fs.makedir("/subdir/m5/bar")
        self.assertEqual(mount_fs.listdir("/subdir/m4"), ["foo"])
        self.assertEqual(mount_fs.listdir("/subdir/m5"), ["bar"])
        self.assertEqual(m4.listdir("/"), ["foo"])
        self.assertEqual(m5.listdir("/"), ["bar"])
        m5.removedir("/bar")
        self.assertEqual(mount_fs.listdir("/subdir/m5"), [])

    def test_auto_close(self):
        """Test MountFS auto close is working"""
        mount_fs = MountFS()
        m1 = MemoryFS()
        m2 = MemoryFS()
        mount_fs.mount("/m1", m1)
        mount_fs.mount("/m2", m2)
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
        mount_fs.mount("/m1", m1)
        mount_fs.mount("/m2", m2)
        self.assertFalse(m1.isclosed())
        self.assertFalse(m2.isclosed())
        mount_fs.close()
        self.assertFalse(m1.isclosed())
        self.assertFalse(m2.isclosed())

    def test_empty(self):
        """Test MountFS with nothing mounted."""
        mount_fs = MountFS()
        self.assertEqual(mount_fs.listdir("/"), [])

    def test_mount_self(self):
        mount_fs = MountFS()
        with self.assertRaises(ValueError):
            mount_fs.mount("/m1", mount_fs)

    def test_desc(self):
        mount_fs = MountFS()
        mount_fs.desc("/")

    def test_makedirs(self):
        mount_fs = MountFS()
        with self.assertRaises(ResourceNotFound):
            mount_fs.makedir("empty")
        m1 = MemoryFS()
        m2 = MemoryFS()
        with self.assertRaises(ResourceNotFound):
            mount_fs.makedirs("/m1/foo/bar", recreate=True)
        mount_fs.mount("/m1", m1)
        mount_fs.makedirs("/m1/foo/bar", recreate=True)
        self.assertEqual(m1.listdir("foo"), ["bar"])
        with self.assertRaises(ResourceNotFound):
            mount_fs.makedirs("/subdir/m2/bar/foo", recreate=True)
        mount_fs.mount("/subdir/m2", m2)
        mount_fs.makedirs("/subdir/m2/bar/foo", recreate=True)
        self.assertEqual(m2.listdir("bar"), ["foo"])
        with self.assertRaises(ResourceNotFound):
            mount_fs.makedir("/subdir/m3", recreate=True)

    def test_unmount(self):
        mount_fs = MountFS()
        m1 = MemoryFS()
        m2 = MemoryFS()
        m3 = MemoryFS()
        m4 = MemoryFS()
        mount_fs.mount("/m1", m1)
        with self.assertRaises(ValueError):
            mount_fs.unmount("/m2")
        mount_fs.mount("/m2", m2)
        self.assertEqual(sorted(mount_fs.listdir("/")), ["m1", "m2"])
        mount_fs.unmount("/m1")
        with self.assertRaises(ResourceNotFound):
            mount_fs.listdir("/m1")
        self.assertEqual(mount_fs.listdir("/"), ["m2"])
        with self.assertRaises(ValueError):
            mount_fs.unmount("/m1")
        mount_fs.mount("/subdir/m3", m3)
        with self.assertRaises(ValueError):
            mount_fs.unmount("/subdir")
        mount_fs.mount("/subdir/m4", m4)
        self.assertEqual(sorted(mount_fs.listdir("/")), ["m2", "subdir"])
        mount_fs.makedir("/subdir/m4/foo")
        with self.assertRaises(ValueError):
            mount_fs.unmount("/subdir/m4/foo")
        mount_fs.unmount("/subdir/m4")
        self.assertEqual(sorted(mount_fs.listdir("/")), ["m2", "subdir"])
        self.assertEqual(mount_fs.listdir("/subdir"), ["m3"])
        mount_fs.unmount("/subdir/m3")
        self.assertEqual(mount_fs.listdir("/"), ["m2"])
        with self.assertRaises(ResourceNotFound):
            mount_fs.listdir("/subdir")
