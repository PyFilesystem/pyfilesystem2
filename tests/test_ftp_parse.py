from __future__ import unicode_literals

from datetime import datetime
import mock
import time
import unittest

from fs import _ftp_parse as ftp_parse

time2017 = time.struct_time([2017, 11, 28, 1, 1, 1, 1, 332, 0])


class TestFTPParse(unittest.TestCase):

    @mock.patch("time.localtime")
    def test_parse_time(self, mock_localtime):
        self.assertEqual(
            ftp_parse._parse_time('JUL 05 1974'),
            142214400.0
        )

        mock_localtime.return_value = time2017
        self.assertEqual(
            ftp_parse._parse_time('JUL 05 02:00'),
            1499220000.0
        )

        self.assertEqual(
            ftp_parse._parse_time("notadate"),
            None
        )

    def test_parse(self):
        self.assertEqual(ftp_parse.parse(['']), [])

    def test_parse_line(self):
        self.assertIs(ftp_parse.parse_line('not a dir'), None)

    @mock.patch("time.localtime")
    def test_decode_linux(self, mock_localtime):
        mock_localtime.return_value = time2017
        directory = """\
lrwxrwxrwx    1 0        0              19 Jan 18  2006 debian -> ./pub/mirror/debian
drwxr-xr-x   10 0        0            4096 Aug 03 09:21 debian-archive
lrwxrwxrwx    1 0        0              27 Nov 30  2015 debian-backports -> pub/mirror/debian-backports
drwxr-xr-x   12 0        0            4096 Sep 29 13:13 pub
-rw-r--r--    1 0        0              26 Mar 04  2010 robots.txt
drwxr-xr-x   8 foo      bar          4096 Oct  4 09:05 test
drwxr-xr-x   2 foo-user foo-group         0 Jan  5 11:59 240485
"""

        expected = [{u'access': {u'group': u'0',
              u'permissions': [u'g_r',
                               u'g_w',
                               u'g_x',
                               u'o_r',
                               u'o_w',
                               u'o_x',
                               u'u_r',
                               u'u_w',
                               u'u_x'],
              u'user': u'0'},
  u'basic': {u'is_dir': True, u'name': u'debian'},
  u'details': {u'modified': 1137542400.0, u'size': 19, u'type': 1},
  u'ftp': {u'ls': u'lrwxrwxrwx    1 0        0              19 Jan 18  2006 debian -> ./pub/mirror/debian'}},
 {u'access': {u'group': u'0',
              u'permissions': [u'g_r',
                               u'g_x',
                               u'o_r',
                               u'o_x',
                               u'u_r',
                               u'u_w',
                               u'u_x'],
              u'user': u'0'},
  u'basic': {u'is_dir': True, u'name': u'debian-archive'},
  u'details': {u'modified': 1501752060.0, u'size': 4096, u'type': 1},
  u'ftp': {u'ls': u'drwxr-xr-x   10 0        0            4096 Aug 03 09:21 debian-archive'}},
 {u'access': {u'group': u'0',
              u'permissions': [u'g_r',
                               u'g_w',
                               u'g_x',
                               u'o_r',
                               u'o_w',
                               u'o_x',
                               u'u_r',
                               u'u_w',
                               u'u_x'],
              u'user': u'0'},
  u'basic': {u'is_dir': True, u'name': u'debian-backports'},
  u'details': {u'modified': 1448841600.0, u'size': 27, u'type': 1},
  u'ftp': {u'ls': u'lrwxrwxrwx    1 0        0              27 Nov 30  2015 debian-backports -> pub/mirror/debian-backports'}},
 {u'access': {u'group': u'0',
              u'permissions': [u'g_r',
                               u'g_x',
                               u'o_r',
                               u'o_x',
                               u'u_r',
                               u'u_w',
                               u'u_x'],
              u'user': u'0'},
  u'basic': {u'is_dir': True, u'name': u'pub'},
  u'details': {u'modified': 1506690780.0, u'size': 4096, u'type': 1},
  u'ftp': {u'ls': u'drwxr-xr-x   12 0        0            4096 Sep 29 13:13 pub'}},
 {u'access': {u'group': u'0',
              u'permissions': [u'g_r', u'o_r', u'u_r', u'u_w'],
              u'user': u'0'},
  u'basic': {u'is_dir': False, u'name': u'robots.txt'},
  u'details': {u'modified': 1267660800.0, u'size': 26, u'type': 2},
  u'ftp': {u'ls': u'-rw-r--r--    1 0        0              26 Mar 04  2010 robots.txt'}},
 {u'access': {u'group': u'bar',
              u'permissions': [u'g_r',
                               u'g_x',
                               u'o_r',
                               u'o_x',
                               u'u_r',
                               u'u_w',
                               u'u_x'],
              u'user': u'foo'},
  u'basic': {u'is_dir': True, u'name': u'test'},
  u'details': {u'modified': 1507107900.0, u'size': 4096, u'type': 1},
  u'ftp': {u'ls': u'drwxr-xr-x   8 foo      bar          4096 Oct  4 09:05 test'}},
{u'access': {u'group': u'foo-group',
              u'permissions': [u'g_r',
                               u'g_x',
                               u'o_r',
                               u'o_x',
                               u'u_r',
                               u'u_w',
                               u'u_x'],
              u'user': u'foo-user'},
  u'basic': {u'is_dir': True, u'name': u'240485'},
  u'details': {u'modified': 1483617540.0, u'size': 0, u'type': 1},
  u'ftp': {u'ls': u'drwxr-xr-x   2 foo-user foo-group         0 Jan  5 11:59 240485'}}]

        parsed = ftp_parse.parse(directory.splitlines())
        self.assertEqual(parsed, expected)
