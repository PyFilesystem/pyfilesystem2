from __future__ import unicode_literals

import os
import mock
import tempfile
import unittest
import pkg_resources

import six

from fs import open_fs, opener
from fs.osfs import OSFS
from fs.opener import registry, errors
from fs.memoryfs import MemoryFS
from fs.appfs import UserDataFS
from fs.opener.parse import ParseResult


class TestParse(unittest.TestCase):

    def test_registry_repr(self):
        str(registry)
        repr(registry)

    def test_parse_not_url(self):
        with self.assertRaises(errors.ParseError):
            parsed = opener.parse('foo/bar')

    def test_parse_simple(self):
        parsed = opener.parse('osfs://foo/bar')
        expected = ParseResult(
            'osfs',
            None,
            None,
            'foo/bar',
            {},
            None
        )
        self.assertEqual(expected, parsed)

    def test_parse_credentials(self):
        parsed = opener.parse('ftp://user:pass@ftp.example.org')
        expected = ParseResult(
            'ftp',
            'user',
            'pass',
            'ftp.example.org',
            {},
            None
        )
        self.assertEqual(expected, parsed)

        parsed = opener.parse('ftp://user@ftp.example.org')
        expected = ParseResult(
            'ftp',
            'user',
            '',
            'ftp.example.org',
            {},
            None
        )
        self.assertEqual(expected, parsed)

    def test_parse_path(self):
        parsed = opener.parse('osfs://foo/bar!example.txt')
        expected = ParseResult(
            'osfs',
            None,
            None,
            'foo/bar',
            {},
            'example.txt'
        )
        self.assertEqual(expected, parsed)

    def test_parse_params(self):
        parsed = opener.parse('ftp://ftp.example.org?proxy=ftp.proxy.org')
        expected = ParseResult(
            'ftp',
            None,
            None,
            'ftp.example.org',
            {
                'proxy':'ftp.proxy.org'
            },
            None
        )
        self.assertEqual(expected, parsed)

    def test_parse_params_multiple(self):
        parsed = opener.parse('ftp://ftp.example.org?foo&bar=1')
        expected = ParseResult(
            'ftp',
            None,
            None,
            'ftp.example.org',
            {
                'foo':'',
                'bar':'1'
            },
            None
        )
        self.assertEqual(expected, parsed)

    def test_parse_user_password_proxy(self):
        parsed = opener.parse('ftp://user:password@ftp.example.org?proxy=ftp.proxy.org')
        expected = ParseResult(
            'ftp',
            'user',
            'password',
            'ftp.example.org',
            {
                'proxy': 'ftp.proxy.org'
            },
            None
        )
        self.assertEqual(expected, parsed)

    def test_parse_user_password_decode(self):
        parsed = opener.parse('ftp://user%40large:password@ftp.example.org')
        expected = ParseResult(
            'ftp',
            'user@large',
            'password',
            'ftp.example.org',
            {},
            None
        )
        self.assertEqual(expected, parsed)

    def test_parse_resource_decode(self):
        parsed = opener.parse('ftp://user%40large:password@ftp.example.org/%7Econnolly')
        expected = ParseResult(
            'ftp',
            'user@large',
            'password',
            'ftp.example.org/~connolly',
            {},
            None
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
            with opener.open_fs('zip://' + zip_name, writeable=False) as zip_fs:
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
            with opener.open_fs('tar://' + tar_name, writeable=False) as tar_fs:
                self.assertEqual(tar_fs.gettext('foo.txt'), 'foofoo')
        finally:
            os.remove(tar_name)

    def test_open_fs(self):
        mem_fs = opener.open_fs("mem://")
        mem_fs_2 = opener.open_fs(mem_fs)
        self.assertEqual(mem_fs, mem_fs_2)

    def test_open_userdata(self):
        with self.assertRaises(errors.OpenerError):
            opener.open_fs('userdata://foo:bar:baz:egg')

        app_fs = opener.open_fs(
            'userdata://fstest:willmcgugan:1.0',
            create=True
        )
        self.assertEqual(app_fs.app_dirs.appname, 'fstest')
        self.assertEqual(app_fs.app_dirs.appauthor, 'willmcgugan')
        self.assertEqual(app_fs.app_dirs.version, '1.0')

    def test_open_userdata_no_version(self):
        app_fs = opener.open_fs(
            'userdata://fstest:willmcgugan',
            create=True
        )
        self.assertEqual(app_fs.app_dirs.appname, 'fstest')
        self.assertEqual(app_fs.app_dirs.appauthor, 'willmcgugan')
        self.assertEqual(app_fs.app_dirs.version, None)

    def test_user_data_opener(self):
        user_data_fs = open_fs('userdata://fstest:willmcgugan:1.0')
        self.assertIsInstance(user_data_fs, UserDataFS)
        user_data_fs.makedir('foo', recreate=True)
        user_data_fs.settext('foo/bar.txt', 'baz')
        user_data_fs_foo_dir = open_fs('userdata://fstest:willmcgugan:1.0/foo/')
        self.assertEqual(user_data_fs_foo_dir.gettext('bar.txt'), 'baz')

    @mock.patch("fs.ftpfs.FTPFS")
    def test_open_ftp(self, mock_FTPFS):
        open_fs('ftp://foo:bar@ftp.example.org')
        mock_FTPFS.assert_called_once_with('ftp.example.org', passwd='bar', port=21, user='foo', proxy=None)

    @mock.patch("fs.ftpfs.FTPFS")
    def test_open_ftp_proxy(self, mock_FTPFS):
        open_fs('ftp://foo:bar@ftp.example.org?proxy=ftp.proxy.org')
        mock_FTPFS.assert_called_once_with('ftp.example.org', passwd='bar', port=21, user='foo', proxy='ftp.proxy.org')

