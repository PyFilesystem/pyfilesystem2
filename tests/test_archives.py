# -*- encoding: UTF-8
from __future__ import unicode_literals

import os
import stat

from six import text_type

from fs.opener import open_fs
from fs.enums import ResourceType
from fs import walk
from fs import errors
from fs.test import UNICODE_TEXT


class ArchiveTestCases(object):
    def make_source_fs(self):
        return open_fs("temp://")

    def build_source(self, fs):
        fs.makedirs("foo/bar/baz")
        fs.makedir("tmp")
        fs.writetext("Файл", "unicode filename")
        fs.writetext("top.txt", "Hello, World")
        fs.writetext("top2.txt", "Hello, World")
        fs.writetext("foo/bar/egg", "foofoo")
        fs.makedir("unicode")
        fs.writetext("unicode/text.txt", UNICODE_TEXT)

    def compress(self, fs):
        pass

    def load_archive(self):
        pass

    def remove_archive(self):
        pass

    def setUp(self):
        self.source_fs = source_fs = self.make_source_fs()
        self.build_source(source_fs)
        self.compress(source_fs)
        self.fs = self.load_archive()

    def tearDown(self):
        self.source_fs.close()
        self.fs.close()
        self.remove_archive()

    def test_repr(self):
        repr(self.fs)

    def test_str(self):
        self.assertIsInstance(text_type(self.fs), text_type)

    def test_readonly(self):
        with self.assertRaises(errors.ResourceReadOnly):
            self.fs.makedir("newdir")
        with self.assertRaises(errors.ResourceReadOnly):
            self.fs.remove("top.txt")
        with self.assertRaises(errors.ResourceReadOnly):
            self.fs.removedir("foo/bar/baz")
        with self.assertRaises(errors.ResourceReadOnly):
            self.fs.create("foo.txt")
        with self.assertRaises(errors.ResourceReadOnly):
            self.fs.setinfo("foo.txt", {})

    def test_getinfo(self):
        root = self.fs.getinfo("/", ["details"])
        self.assertEqual(root.name, "")
        self.assertTrue(root.is_dir)
        self.assertEqual(root.get("details", "type"), ResourceType.directory)

        bar = self.fs.getinfo("foo/bar", ["details"])
        self.assertEqual(bar.name, "bar")
        self.assertTrue(bar.is_dir)
        self.assertEqual(bar.get("details", "type"), ResourceType.directory)

        top = self.fs.getinfo("top.txt", ["details", "access"])
        self.assertEqual(top.size, 12)
        self.assertFalse(top.is_dir)

        try:
            source_syspath = self.source_fs.getsyspath("/top.txt")
        except errors.NoSysPath:
            pass
        else:
            if top.has_namespace("access"):
                self.assertEqual(
                    top.permissions.mode, stat.S_IMODE(os.stat(source_syspath).st_mode)
                )

        self.assertEqual(top.get("details", "type"), ResourceType.file)

    def test_listdir(self):
        self.assertEqual(
            sorted(self.source_fs.listdir("/")), sorted(self.fs.listdir("/"))
        )
        for name in self.fs.listdir("/"):
            self.assertIsInstance(name, text_type)
        with self.assertRaises(errors.DirectoryExpected):
            self.fs.listdir("top.txt")
        with self.assertRaises(errors.ResourceNotFound):
            self.fs.listdir("nothere")

    def test_open(self):
        with self.fs.open("top.txt") as f:
            chars = []
            while True:
                c = f.read(2)
                if not c:
                    break
                chars.append(c)
            self.assertEqual("".join(chars), "Hello, World")
        with self.assertRaises(errors.ResourceNotFound):
            with self.fs.open("nothere.txt") as f:
                pass
        with self.assertRaises(errors.FileExpected):
            with self.fs.open("foo") as f:
                pass

    def test_gets(self):
        self.assertEqual(self.fs.readtext("top.txt"), "Hello, World")
        self.assertEqual(self.fs.readtext("foo/bar/egg"), "foofoo")
        self.assertEqual(self.fs.readbytes("top.txt"), b"Hello, World")
        self.assertEqual(self.fs.readbytes("foo/bar/egg"), b"foofoo")
        with self.assertRaises(errors.ResourceNotFound):
            self.fs.readbytes("what.txt")

    def test_walk_files(self):
        source_files = sorted(walk.walk_files(self.source_fs))
        archive_files = sorted(walk.walk_files(self.fs))

        self.assertEqual(source_files, archive_files)

    def test_implied_dir(self):
        self.fs.getinfo("foo/bar")
        self.fs.getinfo("foo")
