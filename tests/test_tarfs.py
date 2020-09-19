# -*- encoding: UTF-8
from __future__ import unicode_literals

import os
import six
import tarfile
import tempfile
import unittest
import pytest
from six import BytesIO

from fs import tarfs
from fs.enums import ResourceType
from fs.compress import write_tar
from fs.opener import open_fs
from fs.opener.errors import NotWriteable
from fs.errors import NoURL
from fs.test import FSTestCases

from .test_archives import ArchiveTestCases


class TestWriteReadTarFS(unittest.TestCase):
    def setUp(self):
        fh, self._temp_path = tempfile.mkstemp()
        os.close(fh)

    def tearDown(self):
        os.remove(self._temp_path)

    def test_unicode_paths(self):
        # https://github.com/PyFilesystem/pyfilesystem2/issues/135
        with tarfs.TarFS(self._temp_path, write=True) as tar_fs:
            tar_fs.writetext("Файл", "some content")

        with tarfs.TarFS(self._temp_path) as tar_fs:
            paths = list(tar_fs.walk.files())
            for path in paths:
                self.assertIsInstance(path, six.text_type)
                with tar_fs.openbin(path) as f:
                    f.read()


class TestWriteTarFS(FSTestCases, unittest.TestCase):
    """
    Test TarFS implementation.

    When writing, a TarFS is essentially a TempFS.
    """

    def make_fs(self):
        fh, _tar_file = tempfile.mkstemp()
        os.close(fh)
        fs = tarfs.TarFS(_tar_file, write=True)
        fs._tar_file = _tar_file
        return fs

    def destroy_fs(self, fs):
        fs.close()
        os.remove(fs._tar_file)
        del fs._tar_file


class TestWriteTarFSToFileobj(FSTestCases, unittest.TestCase):
    """
    Test TarFS implementation.

    When writing, a TarFS is essentially a TempFS.

    """

    def make_fs(self):
        _tar_file = six.BytesIO()
        fs = tarfs.TarFS(_tar_file, write=True)
        fs._tar_file = _tar_file
        return fs

    def destroy_fs(self, fs):
        fs.close()
        del fs._tar_file


class TestWriteGZippedTarFS(FSTestCases, unittest.TestCase):
    def make_fs(self):
        fh, _tar_file = tempfile.mkstemp()
        os.close(fh)
        fs = tarfs.TarFS(_tar_file, write=True, compression="gz")
        fs._tar_file = _tar_file
        return fs

    def destroy_fs(self, fs):
        fs.close()
        os.remove(fs._tar_file)
        del fs._tar_file


@pytest.mark.skipif(six.PY2, reason="Python2 does not support LZMA")
class TestWriteXZippedTarFS(FSTestCases, unittest.TestCase):
    def make_fs(self):
        fh, _tar_file = tempfile.mkstemp()
        os.close(fh)
        fs = tarfs.TarFS(_tar_file, write=True, compression="xz")
        fs._tar_file = _tar_file
        return fs

    def destroy_fs(self, fs):
        fs.close()
        self.assert_is_xz(fs)
        os.remove(fs._tar_file)
        del fs._tar_file

    def assert_is_xz(self, fs):
        try:
            tarfile.open(fs._tar_file, "r:xz")
        except tarfile.ReadError:
            self.fail("{} is not a valid xz archive".format(fs._tar_file))
        for other_comps in ["bz2", "gz", ""]:
            with self.assertRaises(tarfile.ReadError):
                tarfile.open(fs._tar_file, "r:{}".format(other_comps))


class TestWriteBZippedTarFS(FSTestCases, unittest.TestCase):
    def make_fs(self):
        fh, _tar_file = tempfile.mkstemp()
        os.close(fh)
        fs = tarfs.TarFS(_tar_file, write=True, compression="bz2")
        fs._tar_file = _tar_file
        return fs

    def destroy_fs(self, fs):
        fs.close()
        self.assert_is_bzip(fs)
        os.remove(fs._tar_file)
        del fs._tar_file

    def assert_is_bzip(self, fs):
        try:
            tarfile.open(fs._tar_file, "r:bz2")
        except tarfile.ReadError:
            self.fail("{} is not a valid bz2 archive".format(fs._tar_file))
        for other_comps in ["gz", ""]:
            with self.assertRaises(tarfile.ReadError):
                tarfile.open(fs._tar_file, "r:{}".format(other_comps))


class TestReadTarFS(ArchiveTestCases, unittest.TestCase):
    """
    Test Reading tar files.

    """

    def compress(self, fs):
        fh, self._temp_path = tempfile.mkstemp()
        os.close(fh)
        write_tar(fs, self._temp_path)

    def load_archive(self):
        return tarfs.TarFS(self._temp_path)

    def remove_archive(self):
        os.remove(self._temp_path)

    def test_read_from_fileobject(self):
        try:
            tarfs.TarFS(open(self._temp_path, "rb"))
        except Exception:
            self.fail("Couldn't open tarfs from fileobject")

    def test_read_from_filename(self):
        try:
            tarfs.TarFS(self._temp_path)
        except Exception:
            self.fail("Couldn't open tarfs from filename")

    def test_read_non_existent_file(self):
        fs = tarfs.TarFS(open(self._temp_path, "rb"))
        # it has been very difficult to catch exception in __del__()
        del fs._tar
        try:
            fs.close()
        except AttributeError:
            self.fail("Could not close tar fs properly")
        except Exception:
            self.fail("Strange exception in closing fs")

    def test_getinfo(self):
        super(TestReadTarFS, self).test_getinfo()
        top = self.fs.getinfo("top.txt", ["tar"])
        self.assertTrue(top.get("tar", "is_file"))

    def test_geturl_for_fs(self):
        test_fixtures = [
            # test_file, expected
            ["foo/bar/egg/foofoo", "foo/bar/egg/foofoo"],
            ["foo/bar egg/foo foo", "foo/bar%20egg/foo%20foo"],
        ]
        tar_file_path = self._temp_path.replace("\\", "/")
        for test_file, expected_file in test_fixtures:
            expected = "tar://{tar_file_path}!/{file_inside_tar}".format(
                tar_file_path=tar_file_path, file_inside_tar=expected_file
            )
            self.assertEqual(self.fs.geturl(test_file, purpose="fs"), expected)

    def test_geturl_for_fs_but_file_is_binaryio(self):
        self.fs._file = six.BytesIO()
        self.assertRaises(NoURL, self.fs.geturl, "test", "fs")

    def test_geturl_for_download(self):
        test_file = "foo/bar/egg/foofoo"
        with self.assertRaises(NoURL):
            self.fs.geturl(test_file)


class TestBrokenPaths(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmpfs = open_fs("temp://tarfstest")

    @classmethod
    def tearDownClass(cls):
        cls.tmpfs.close()

    def setUp(self):
        self.tempfile = self.tmpfs.open("test.tar", "wb+")
        with tarfile.open(mode="w", fileobj=self.tempfile) as tf:
            tf.addfile(tarfile.TarInfo("."))
            tf.addfile(tarfile.TarInfo("../foo.txt"))
        self.tempfile.seek(0)
        self.fs = tarfs.TarFS(self.tempfile)

    def tearDown(self):
        self.fs.close()
        self.tempfile.close()

    def test_listdir(self):
        self.assertEqual(self.fs.listdir("/"), [])


class TestImplicitDirectories(unittest.TestCase):
    """Regression tests for #160."""

    @classmethod
    def setUpClass(cls):
        cls.tmpfs = open_fs("temp://")

    @classmethod
    def tearDownClass(cls):
        cls.tmpfs.close()

    def setUp(self):
        self.tempfile = self.tmpfs.open("test.tar", "wb+")
        with tarfile.open(mode="w", fileobj=self.tempfile) as tf:
            tf.addfile(tarfile.TarInfo("foo/bar/baz/spam.txt"))
            tf.addfile(tarfile.TarInfo("./foo/eggs.bin"))
            tf.addfile(tarfile.TarInfo("./foo/yolk/beans.txt"))
            info = tarfile.TarInfo("foo/yolk")
            info.type = tarfile.DIRTYPE
            tf.addfile(info)
        self.tempfile.seek(0)
        self.fs = tarfs.TarFS(self.tempfile)

    def tearDown(self):
        self.fs.close()
        self.tempfile.close()

    def test_isfile(self):
        self.assertFalse(self.fs.isfile("foo"))
        self.assertFalse(self.fs.isfile("foo/bar"))
        self.assertFalse(self.fs.isfile("foo/bar/baz"))
        self.assertTrue(self.fs.isfile("foo/bar/baz/spam.txt"))
        self.assertTrue(self.fs.isfile("foo/yolk/beans.txt"))
        self.assertTrue(self.fs.isfile("foo/eggs.bin"))
        self.assertFalse(self.fs.isfile("foo/eggs.bin/baz"))

    def test_isdir(self):
        self.assertTrue(self.fs.isdir("foo"))
        self.assertTrue(self.fs.isdir("foo/yolk"))
        self.assertTrue(self.fs.isdir("foo/bar"))
        self.assertTrue(self.fs.isdir("foo/bar/baz"))
        self.assertFalse(self.fs.isdir("foo/bar/baz/spam.txt"))
        self.assertFalse(self.fs.isdir("foo/eggs.bin"))
        self.assertFalse(self.fs.isdir("foo/eggs.bin/baz"))
        self.assertFalse(self.fs.isdir("foo/yolk/beans.txt"))

    def test_listdir(self):
        self.assertEqual(sorted(self.fs.listdir("foo")), ["bar", "eggs.bin", "yolk"])
        self.assertEqual(self.fs.listdir("foo/bar"), ["baz"])
        self.assertEqual(self.fs.listdir("foo/bar/baz"), ["spam.txt"])
        self.assertEqual(self.fs.listdir("foo/yolk"), ["beans.txt"])

    def test_getinfo(self):
        info = self.fs.getdetails("foo/bar/baz")
        self.assertEqual(info.name, "baz")
        self.assertEqual(info.size, 0)
        self.assertIs(info.type, ResourceType.directory)

        info = self.fs.getdetails("foo")
        self.assertEqual(info.name, "foo")
        self.assertEqual(info.size, 0)
        self.assertIs(info.type, ResourceType.directory)


class TestSymlinks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmpfs = open_fs("temp://")

    @classmethod
    def tearDownClass(cls):
        cls.tmpfs.close()

    def setUp(self):
        def _info(name, **kwargs):
            info = tarfile.TarInfo(name)
            for k, v in kwargs.items():
                setattr(info, k, v)
            return info

        # /foo
        # /foo/bar.txt
        # /foo/baz.txt -> /foo/bar.txt
        # /spam -> /foo
        # /eggs
        # /eggs/yolk -> /spam

        self.tempfile = self.tmpfs.open("test.tar", "wb+")
        with tarfile.open(mode="w", fileobj=self.tempfile) as tf:
            tf.addfile(_info("foo", type=tarfile.DIRTYPE))
            buff = BytesIO(b"hello")
            tf.addfile(_info("foo/bar.txt", size=len(buff.getvalue())), buff)
            tf.addfile(_info("foo/baz.txt", type=tarfile.SYMTYPE, linkname="bar.txt"))
            tf.addfile(_info("spam", type=tarfile.SYMTYPE, linkname="foo"))
            tf.addfile(_info("eggs", type=tarfile.DIRTYPE))
            tf.addfile(_info("eggs/yolk", type=tarfile.SYMTYPE, linkname="../spam"))
        self.tempfile.seek(0)
        self.fs = tarfs.TarFS(self.tempfile)

    def tearDown(self):
        self.fs.close()
        self.tempfile.close()

    def test_openbin(self):
        # read an actual file
        with self.fs.openbin("foo/bar.txt") as bar:
            self.assertEqual(bar.read(), b"hello")
        # read a link to an actual file
        with self.fs.openbin("foo/baz.txt") as baz:
            self.assertEqual(baz.read(), b"hello")
        # read an actual file via a linked directory
        with self.fs.openbin("spam/bar.txt") as bar:
            self.assertEqual(bar.read(), b"hello")
        # read a link via a linked directory
        with self.fs.openbin("spam/baz.txt") as baz:
            self.assertEqual(baz.read(), b"hello")

    def test_isfile(self):
        self.assertFalse(self.fs.isfile("foo"))
        self.assertFalse(self.fs.isfile("spam"))
        self.assertFalse(self.fs.isfile("eggs"))
        self.assertFalse(self.fs.isfile("eggs/yolk"))
        self.assertTrue(self.fs.isfile("foo/bar.txt"))
        self.assertTrue(self.fs.isfile("foo/baz.txt"))
        self.assertTrue(self.fs.isfile("eggs/yolk/bar.txt"))
        self.assertTrue(self.fs.isfile("eggs/yolk/baz.txt"))

    def test_isdir(self):
        self.assertTrue(self.fs.isdir("foo"))
        self.assertTrue(self.fs.isdir("spam"))
        self.assertTrue(self.fs.isdir("eggs/yolk"))
        self.assertFalse(self.fs.isdir("foo/bar.txt"))
        self.assertFalse(self.fs.isdir("foo/baz.txt"))
        self.assertFalse(self.fs.isdir("eggs/yolk/bar.txt"))
        self.assertFalse(self.fs.isdir("eggs/yolk/baz.txt"))

    def test_islink(self):
        self.assertFalse(self.fs.islink("foo"))
        self.assertTrue(self.fs.islink("spam"))
        self.assertTrue(self.fs.islink("eggs/yolk"))
        self.assertFalse(self.fs.islink("foo/bar.txt"))
        self.assertTrue(self.fs.islink("foo/baz.txt"))
        self.assertFalse(self.fs.islink("eggs/yolk/bar.txt"))
        self.assertTrue(self.fs.islink("eggs/yolk/baz.txt"))

    def test_getinfo(self):
        file_info = self.fs.getinfo("foo/bar.txt", namespaces=("details", "link"))
        self.assertIn("details", file_info.namespaces)
        self.assertIn("link", file_info.namespaces)
        self.assertFalse(file_info.is_dir)
        self.assertIs(file_info.target, None)
        self.assertEqual(file_info.type, ResourceType.file)

        link_info = self.fs.getinfo("foo/baz.txt", namespaces=("details", "link"))
        self.assertIn("details", link_info.namespaces)
        self.assertIn("link", link_info.namespaces)
        self.assertFalse(link_info.is_dir)
        self.assertEqual(link_info.target, "foo/bar.txt")
        self.assertEqual(link_info.type, ResourceType.symlink)

        dir_info = self.fs.getinfo("foo", namespaces=("details", "link"))
        self.assertIn("details", dir_info.namespaces)
        self.assertIn("link", dir_info.namespaces)
        self.assertTrue(dir_info.is_dir)
        self.assertEqual(dir_info.target, None)
        self.assertEqual(dir_info.type, ResourceType.directory)

        dirlink_info = self.fs.getinfo("spam", namespaces=("details", "link"))
        self.assertIn("details", dirlink_info.namespaces)
        self.assertIn("link", dirlink_info.namespaces)
        self.assertTrue(dirlink_info.is_dir)
        self.assertEqual(dirlink_info.target, "foo")
        self.assertEqual(dirlink_info.type, ResourceType.symlink)

    def test_listdir(self):
        self.assertEqual(sorted(self.fs.listdir("foo")), ["bar.txt", "baz.txt"])
        self.assertEqual(sorted(self.fs.listdir("spam")), ["bar.txt", "baz.txt"])


class TestReadTarFSMem(TestReadTarFS):
    def make_source_fs(self):
        return open_fs("mem://")


class TestOpener(unittest.TestCase):
    def test_not_writeable(self):
        with self.assertRaises(NotWriteable):
            open_fs("tar://foo.zip", writeable=True)
