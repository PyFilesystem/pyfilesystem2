from __future__ import unicode_literals

import os
import tempfile
import unittest

from fs import opener
from fs.osfs import OSFS
from fs.memoryfs import MemoryFS


class TestParse(unittest.TestCase):

    def test_parse_not_url(self):
        with self.assertRaises(opener.ParseError):
            parsed = opener.parse('foo/bar')

    def test_parse_simple(self):
        parsed = opener.parse('osfs://foo/bar')
        expected = opener.registry.ParseResult(
            'osfs',
            None,
            None,
            'foo/bar',
            None
        )
        self.assertEqual(expected, parsed)

    def test_parse_credentials(self):
        parsed = opener.parse('ftp://user:pass@ftp.example.org')
        expected = opener.registry.ParseResult(
            'ftp',
            'user',
            'pass',
            'ftp.example.org',
            None
        )
        self.assertEqual(expected, parsed)

        parsed = opener.parse('ftp://user@ftp.example.org')
        expected = opener.registry.ParseResult(
            'ftp',
            'user',
            '',
            'ftp.example.org',
            None
        )
        self.assertEqual(expected, parsed)

    def test_parse_path(self):
        parsed = opener.parse('osfs://foo/bar!example.txt')
        expected = opener.registry.ParseResult(
            'osfs',
            None,
            None,
            'foo/bar',
            'example.txt'
        )
        self.assertEqual(expected, parsed)


class TestRegistry(unittest.TestCase):

    def test_empty(self):
        registry = opener.Registry()
        with self.assertRaises(opener.Unsupported):
            registry.open_fs('osfs:///')

    def test_open_osfs(self):
        fs = opener.open_fs("osfs://.")
        self.assertIsInstance(fs, OSFS)

        # test default protocol
        fs = opener.open_fs("./")
        self.assertIsInstance(fs, OSFS)

    def test_open_memfs(self):
        fs = opener.open_fs("mem://")
        self.assertIsInstance(fs, MemoryFS)

    def test_open_zipfs(self):
        fh, zip_name = tempfile.mkstemp()
        os.close(fh)
        try:
            # Test creating zip
            with opener.open_fs('zip://' + zip_name, create=True) as make_zip:
                make_zip.settext('foo.txt', 'foofoo')
            # Test opening zip
            with opener.open_fs('zip://' + zip_name) as zip_fs:
                self.assertEqual(zip_fs.gettext('foo.txt'), 'foofoo')
        finally:
            os.remove(zip_name)

    def test_open_tarfs(self):
        fh, tar_name = tempfile.mkstemp(suffix='.tar.gz')
        os.close(fh)
        try:
            # Test creating tar
            with opener.open_fs('tar://' + tar_name, create=True) as make_tar:
                self.assertEqual(make_tar.compression, 'gz')
                make_tar.settext('foo.txt', 'foofoo')
            # Test opening tar
            with opener.open_fs('tar://' + tar_name) as tar_fs:
                self.assertEqual(tar_fs.gettext('foo.txt'), 'foofoo')
        finally:
            os.remove(tar_name)

    def test_open_fs(self):
        mem_fs = opener.open_fs("mem://")
        mem_fs_2 = opener.open_fs(mem_fs)
        self.assertEqual(mem_fs, mem_fs_2)


class TestManageFS(unittest.TestCase):

    def test_manage_fs_url(self):
        with opener.manage_fs('mem://') as mem_fs:
            self.assertIsInstance(mem_fs, MemoryFS)
        self.assertTrue(mem_fs.isclosed())

    def test_manage_fs_obj(self):
        mem_fs = MemoryFS()
        with opener.manage_fs(mem_fs) as open_mem_fs:
            self.assertIs(mem_fs, open_mem_fs)
        self.assertFalse(mem_fs.isclosed())

    def test_manage_fs_error(self):
        try:
            with opener.manage_fs('mem://') as mem_fs:
                1/0
        except ZeroDivisionError:
            pass

        self.assertTrue(mem_fs.isclosed())

class TestOpeners(unittest.TestCase):

    def test_repr(self):
        # Check __repr__ works
        for _opener in opener.registry.protocols.values():
            repr(_opener)
