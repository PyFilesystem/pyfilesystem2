from __future__ import unicode_literals

import os
import six
import mock
import tempfile
import unittest
import pkg_resources

from fs import opener
from fs.osfs import OSFS
from fs.opener import registry, errors
from fs.memoryfs import MemoryFS


class TestParse(unittest.TestCase):

    def test_registry_repr(self):
        str(registry)
        repr(registry)

    def test_parse_not_url(self):
        with self.assertRaises(errors.ParseError):
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

    def test_registry_protocols(self):
        # Check registry.protocols list the names of all available entry points

        protocols = [
            entry_point.name
            for entry_point in
            pkg_resources.iter_entry_points('fs.opener')
        ]

        self.assertEqual(
            sorted(protocols),
            sorted(opener.registry.protocols)
        )

    def test_unknown_protocol(self):
        with self.assertRaises(errors.UnsupportedProtocol):
            opener.open_fs('unknown://')

    def test_entry_point_load_error(self):

        entry_point = mock.MagicMock()
        entry_point.load.side_effect = ValueError("some error")

        iter_entry_points = mock.MagicMock(return_value=iter([entry_point]))

        with mock.patch('pkg_resources.iter_entry_points', iter_entry_points):
            with self.assertRaises(errors.EntryPointError) as ctx:
                opener.open_fs('test://')
            self.assertEqual(
                'could not load entry point; some error', str(ctx.exception))

    def test_entry_point_type_error(self):

        entry_point = mock.MagicMock()

        iter_entry_points = mock.MagicMock(return_value=iter([entry_point]))

        with mock.patch('pkg_resources.iter_entry_points', iter_entry_points):
            with self.assertRaises(errors.EntryPointError) as ctx:
                opener.open_fs('test://')
            self.assertEqual(
                'entry point did not return an opener', str(ctx.exception))

    def test_entry_point_create_error(self):

        entry_point = mock.MagicMock()
        entry_point.load = mock.MagicMock(return_value=entry_point)
        entry_point.side_effect = ValueError("some creation error")

        iter_entry_points = mock.MagicMock(return_value=iter([entry_point]))
        builtins = 'builtins' if six.PY3 else '__builtin__'

        with mock.patch('pkg_resources.iter_entry_points', iter_entry_points):
            with mock.patch(builtins+'.issubclass', return_value=True):
                with self.assertRaises(errors.EntryPointError) as ctx:
                    opener.open_fs('test://')
            self.assertEqual(
                'could not instantiate opener; some creation error', str(ctx.exception))


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
        for entry_point in pkg_resources.iter_entry_points('fs.opener'):
            _opener = entry_point.load()
            repr(_opener())

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
