from __future__ import unicode_literals

import unittest

from fs.mirror import mirror
from fs import open_fs


class TestMirror(unittest.TestCase):
    WORKERS = 0  # Single threaded

    def _contents(self, fs):
        """Extract an FS in to a simple data structure."""
        contents = []
        for path, dirs, files in fs.walk():
            for info in dirs:
                _path = info.make_path(path)
                contents.append((_path, "dir", b""))
            for info in files:
                _path = info.make_path(path)
                contents.append((_path, "file", fs.readbytes(_path)))
        return sorted(contents)

    def assert_compare_fs(self, fs1, fs2):
        """Assert filesystems and contents are the same."""
        self.assertEqual(self._contents(fs1), self._contents(fs2))

    def test_empty_mirror(self):
        m1 = open_fs("mem://")
        m2 = open_fs("mem://")
        mirror(m1, m2, workers=self.WORKERS)
        self.assert_compare_fs(m1, m2)

    def test_mirror_one_file(self):
        m1 = open_fs("mem://")
        m1.writetext("foo", "hello")
        m2 = open_fs("mem://")
        mirror(m1, m2, workers=self.WORKERS)
        self.assert_compare_fs(m1, m2)

    def test_mirror_one_file_one_dir(self):
        m1 = open_fs("mem://")
        m1.writetext("foo", "hello")
        m1.makedir("bar")
        m2 = open_fs("mem://")
        mirror(m1, m2, workers=self.WORKERS)
        self.assert_compare_fs(m1, m2)

    def test_mirror_delete_replace(self):
        m1 = open_fs("mem://")
        m1.writetext("foo", "hello")
        m1.makedir("bar")
        m2 = open_fs("mem://")
        mirror(m1, m2, workers=self.WORKERS)
        self.assert_compare_fs(m1, m2)
        m2.remove("foo")
        mirror(m1, m2, workers=self.WORKERS)
        self.assert_compare_fs(m1, m2)
        m2.removedir("bar")
        mirror(m1, m2, workers=self.WORKERS)
        self.assert_compare_fs(m1, m2)

    def test_mirror_extra_dir(self):
        m1 = open_fs("mem://")
        m1.writetext("foo", "hello")
        m1.makedir("bar")
        m2 = open_fs("mem://")
        m2.makedir("baz")
        mirror(m1, m2, workers=self.WORKERS)
        self.assert_compare_fs(m1, m2)

    def test_mirror_extra_file(self):
        m1 = open_fs("mem://")
        m1.writetext("foo", "hello")
        m1.makedir("bar")
        m2 = open_fs("mem://")
        m2.makedir("baz")
        m2.touch("egg")
        mirror(m1, m2, workers=self.WORKERS)
        self.assert_compare_fs(m1, m2)

    def test_mirror_wrong_type(self):
        m1 = open_fs("mem://")
        m1.writetext("foo", "hello")
        m1.makedir("bar")
        m2 = open_fs("mem://")
        m2.makedir("foo")
        m2.touch("bar")
        mirror(m1, m2, workers=self.WORKERS)
        self.assert_compare_fs(m1, m2)

    def test_mirror_update(self):
        m1 = open_fs("mem://")
        m1.writetext("foo", "hello")
        m1.makedir("bar")
        m2 = open_fs("mem://")
        mirror(m1, m2, workers=self.WORKERS)
        self.assert_compare_fs(m1, m2)
        m2.appendtext("foo", " world!")
        mirror(m1, m2, workers=self.WORKERS)
        self.assert_compare_fs(m1, m2)


class TestMirrorWorkers1(TestMirror):
    WORKERS = 1


class TestMirrorWorkers2(TestMirror):
    WORKERS = 2


class TestMirrorWorkers4(TestMirror):
    WORKERS = 4
