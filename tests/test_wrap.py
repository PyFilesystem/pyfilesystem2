from __future__ import unicode_literals

import operator
import unittest

try:
    from unittest import mock
except ImportError:
    import mock

import six

import fs.copy
import fs.errors
import fs.mirror
import fs.move
import fs.wrap
from fs import open_fs
from fs.info import Info


class TestWrapReadOnly(unittest.TestCase):
    def setUp(self):
        self.fs = open_fs("mem://")
        self.ro = fs.wrap.read_only(self.fs)

    def tearDown(self):
        self.fs.close()

    def assertReadOnly(self, func, *args, **kwargs):
        self.assertRaises(fs.errors.ResourceReadOnly, func, *args, **kwargs)

    def test_open_w(self):
        self.assertReadOnly(self.ro.open, "foo", "w")

    def test_appendtext(self):
        self.assertReadOnly(self.ro.appendtext, "foo", "bar")

    def test_appendbytes(self):
        self.assertReadOnly(self.ro.appendbytes, "foo", b"bar")

    def test_makedir(self):
        self.assertReadOnly(self.ro.makedir, "foo")

    def test_move(self):
        self.assertReadOnly(self.ro.move, "foo", "bar")

    def test_openbin_w(self):
        self.assertReadOnly(self.ro.openbin, "foo", "w")

    def test_remove(self):
        self.assertReadOnly(self.ro.remove, "foo")

    def test_removedir(self):
        self.assertReadOnly(self.ro.removedir, "foo")

    def test_removetree(self):
        self.assertReadOnly(self.ro.removetree, "foo")

    def test_setinfo(self):
        self.assertReadOnly(self.ro.setinfo, "foo", {})

    def test_settimes(self):
        self.assertReadOnly(self.ro.settimes, "foo", {})

    def test_copy(self):
        self.assertReadOnly(self.ro.copy, "foo", "bar")

    def test_create(self):
        self.assertReadOnly(self.ro.create, "foo")

    def test_writetext(self):
        self.assertReadOnly(self.ro.writetext, "foo", "bar")

    def test_writebytes(self):
        self.assertReadOnly(self.ro.writebytes, "foo", b"bar")

    def test_makedirs(self):
        self.assertReadOnly(self.ro.makedirs, "foo/bar")

    def test_touch(self):
        self.assertReadOnly(self.ro.touch, "foo")

    def test_upload(self):
        self.assertReadOnly(self.ro.upload, "foo", six.BytesIO())

    def test_writefile(self):
        self.assertReadOnly(self.ro.writefile, "foo", six.StringIO())

    def test_openbin_r(self):
        self.fs.writebytes("file", b"read me")
        with self.ro.openbin("file") as read_file:
            self.assertEqual(read_file.read(), b"read me")

    def test_open_r(self):
        self.fs.writebytes("file", b"read me")
        with self.ro.open("file", "rb") as read_file:
            self.assertEqual(read_file.read(), b"read me")


class TestWrapReadOnlySyspath(unittest.TestCase):
    # If the wrapped fs has a syspath, there is a chance that somewhere
    # in fs.copy or fs.mirror we try to use it to our advantage, but
    # we want to make sure these implementations don't circumvent the
    # wrapper.

    def setUp(self):
        self.fs = open_fs("temp://")
        self.ro = fs.wrap.read_only(self.fs)
        self.src = open_fs("temp://")
        self.src.touch("foo")
        self.src.makedir("bar")

    def tearDown(self):
        self.fs.close()
        self.src.close()

    def assertReadOnly(self, func, *args, **kwargs):
        self.assertRaises(fs.errors.ResourceReadOnly, func, *args, **kwargs)

    def test_copy_fs(self):
        self.assertReadOnly(fs.copy.copy_fs, self.src, self.ro)

    def test_copy_fs_if_newer(self):
        self.assertReadOnly(fs.copy.copy_fs_if_newer, self.src, self.ro)

    def test_copy_file(self):
        self.assertReadOnly(fs.copy.copy_file, self.src, "foo", self.ro, "foo")

    def test_copy_file_if_newer(self):
        self.assertReadOnly(fs.copy.copy_file_if_newer, self.src, "foo", self.ro, "foo")

    def test_copy_structure(self):
        self.assertReadOnly(fs.copy.copy_structure, self.src, self.ro)

    def test_mirror(self):
        self.assertReadOnly(fs.mirror.mirror, self.src, self.ro)
        fs.mirror.mirror(self.src, self.fs)
        self.fs.touch("baz")
        self.assertReadOnly(fs.mirror.mirror, self.src, self.ro)

    def test_move_fs(self):
        self.assertReadOnly(fs.move.move_fs, self.src, self.ro)
        self.src.removetree("/")
        self.fs.touch("foo")
        self.assertReadOnly(fs.move.move_fs, self.ro, self.src)

    def test_move_file(self):
        self.assertReadOnly(fs.move.move_file, self.src, "foo", self.ro, "foo")
        self.fs.touch("baz")
        self.assertReadOnly(fs.move.move_file, self.ro, "baz", self.src, "foo")

    def test_move_dir(self):
        self.assertReadOnly(fs.move.move_file, self.src, "bar", self.ro, "bar")
        self.fs.makedir("baz")
        self.assertReadOnly(fs.move.move_dir, self.ro, "baz", self.src, "baz")


class TestWrapCachedDir(unittest.TestCase):
    def setUp(self):
        self.fs = open_fs("mem://")
        self.fs.makedirs("foo/bar/baz")
        self.fs.touch("egg")
        self.cached = fs.wrap.cache_directory(self.fs)

    def tearDown(self):
        self.fs.close()

    def assertNotFound(self, func, *args, **kwargs):
        self.assertRaises(fs.errors.ResourceNotFound, func, *args, **kwargs)

    def test_scandir(self):
        key = operator.attrgetter("name")
        expected = [
            Info({"basic": {"name": "egg", "is_dir": False}}),
            Info({"basic": {"name": "foo", "is_dir": True}}),
        ]
        with mock.patch.object(self.fs, "scandir", wraps=self.fs.scandir) as scandir:
            self.assertEqual(sorted(self.cached.scandir("/"), key=key), expected)
            scandir.assert_has_calls([mock.call("/", namespaces=None, page=None)])
        with mock.patch.object(self.fs, "scandir", wraps=self.fs.scandir) as scandir:
            self.assertEqual(sorted(self.cached.scandir("/"), key=key), expected)
            scandir.assert_not_called()

    def test_isdir(self):
        with mock.patch.object(self.fs, "scandir", wraps=self.fs.scandir) as scandir:
            self.assertTrue(self.cached.isdir("foo"))
            self.assertFalse(self.cached.isdir("egg"))  # is file
            self.assertFalse(self.cached.isdir("spam"))  # doesn't exist
            scandir.assert_has_calls([mock.call("/", namespaces=None, page=None)])
        with mock.patch.object(self.fs, "scandir", wraps=self.fs.scandir) as scandir:
            self.assertTrue(self.cached.isdir("foo"))
            self.assertFalse(self.cached.isdir("egg"))
            self.assertFalse(self.cached.isdir("spam"))
            scandir.assert_not_called()

    def test_isfile(self):
        with mock.patch.object(self.fs, "scandir", wraps=self.fs.scandir) as scandir:
            self.assertTrue(self.cached.isfile("egg"))
            self.assertFalse(self.cached.isfile("foo"))  # is dir
            self.assertFalse(self.cached.isfile("spam"))  # doesn't exist
            scandir.assert_has_calls([mock.call("/", namespaces=None, page=None)])
        with mock.patch.object(self.fs, "scandir", wraps=self.fs.scandir) as scandir:
            self.assertTrue(self.cached.isfile("egg"))
            self.assertFalse(self.cached.isfile("foo"))
            self.assertFalse(self.cached.isfile("spam"))
            scandir.assert_not_called()

    def test_getinfo(self):
        with mock.patch.object(self.fs, "scandir", wraps=self.fs.scandir) as scandir:
            self.assertEqual(self.cached.getinfo("foo"), self.fs.getinfo("foo"))
            self.assertEqual(self.cached.getinfo("/"), self.fs.getinfo("/"))
            self.assertNotFound(self.cached.getinfo, "spam")
            scandir.assert_has_calls([mock.call("/", namespaces=None, page=None)])
        with mock.patch.object(self.fs, "scandir", wraps=self.fs.scandir) as scandir:
            self.assertEqual(self.cached.getinfo("foo"), self.fs.getinfo("foo"))
            self.assertEqual(self.cached.getinfo("/"), self.fs.getinfo("/"))
            self.assertNotFound(self.cached.getinfo, "spam")
            scandir.assert_not_called()
