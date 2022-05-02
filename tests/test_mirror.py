from __future__ import unicode_literals

import unittest
from parameterized import parameterized_class

from fs import open_fs
from fs.mirror import mirror


@parameterized_class(("WORKERS",), [(0,), (1,), (2,), (4,)])
class TestMirror(unittest.TestCase):
    def _contents(self, fs):
        """Extract an FS in to a simple data structure."""
        namespaces = ("details", "metadata_changed", "modified")
        contents = []
        for path, dirs, files in fs.walk():
            for info in dirs:
                _path = info.make_path(path)
                contents.append((_path, "dir", b""))
            for info in files:
                _path = info.make_path(path)
                _bytes = fs.readbytes(_path)
                _info = fs.getinfo(_path, namespaces)
                contents.append(
                    (
                        _path,
                        "file",
                        _bytes,
                        _info.modified,
                        _info.metadata_changed,
                    )
                )
        return sorted(contents)

    def assert_compare_fs(self, fs1, fs2):
        """Assert filesystems and contents are the same."""
        self.assertEqual(self._contents(fs1), self._contents(fs2))

    def test_empty_mirror(self):
        m1 = open_fs("mem://")
        m2 = open_fs("mem://")
        mirror(m1, m2, workers=self.WORKERS, preserve_time=True)
        self.assert_compare_fs(m1, m2)

    def test_mirror_one_file(self):
        m1 = open_fs("mem://")
        m1.writetext("foo", "hello")
        m2 = open_fs("mem://")
        mirror(m1, m2, workers=self.WORKERS, preserve_time=True)
        self.assert_compare_fs(m1, m2)

    def test_mirror_one_file_one_dir(self):
        m1 = open_fs("mem://")
        m1.writetext("foo", "hello")
        m1.makedir("bar")
        m2 = open_fs("mem://")
        mirror(m1, m2, workers=self.WORKERS, preserve_time=True)
        self.assert_compare_fs(m1, m2)

    def test_mirror_delete_replace(self):
        m1 = open_fs("mem://")
        m1.writetext("foo", "hello")
        m1.makedir("bar")
        m2 = open_fs("mem://")
        mirror(m1, m2, workers=self.WORKERS, preserve_time=True)
        self.assert_compare_fs(m1, m2)
        m2.remove("foo")
        mirror(m1, m2, workers=self.WORKERS, preserve_time=True)
        self.assert_compare_fs(m1, m2)
        m2.removedir("bar")
        mirror(m1, m2, workers=self.WORKERS, preserve_time=True)
        self.assert_compare_fs(m1, m2)

    def test_mirror_extra_dir(self):
        m1 = open_fs("mem://")
        m1.writetext("foo", "hello")
        m1.makedir("bar")
        m2 = open_fs("mem://")
        m2.makedir("baz")
        mirror(m1, m2, workers=self.WORKERS, preserve_time=True)
        self.assert_compare_fs(m1, m2)

    def test_mirror_extra_file(self):
        m1 = open_fs("mem://")
        m1.writetext("foo", "hello")
        m1.makedir("bar")
        m2 = open_fs("mem://")
        m2.makedir("baz")
        m2.touch("egg")
        mirror(m1, m2, workers=self.WORKERS, preserve_time=True)
        self.assert_compare_fs(m1, m2)

    def test_mirror_wrong_type(self):
        m1 = open_fs("mem://")
        m1.writetext("foo", "hello")
        m1.makedir("bar")
        m2 = open_fs("mem://")
        m2.makedir("foo")
        m2.touch("bar")
        mirror(m1, m2, workers=self.WORKERS, preserve_time=True)
        self.assert_compare_fs(m1, m2)

    def test_mirror_update(self):
        m1 = open_fs("mem://")
        m1.writetext("foo", "hello")
        m1.makedir("bar")
        m2 = open_fs("mem://")
        mirror(m1, m2, workers=self.WORKERS, preserve_time=True)
        self.assert_compare_fs(m1, m2)
        m2.appendtext("foo", " world!")
        mirror(m1, m2, workers=self.WORKERS, preserve_time=True)
        self.assert_compare_fs(m1, m2)
