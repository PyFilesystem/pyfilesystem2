from __future__ import unicode_literals

from datetime import datetime
import time
import unittest

from fs import _ftp_parse as ftp_parse


class TestFTPParse(unittest.TestCase):

    def test_parse_time(self):
        self.assertEqual(
            ftp_parse._parse_time('JUL 05 1974'),
            142214400.0
        )

        year = time.localtime().tm_year
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

    def test_decode_linux(self):
        directory = """\
lrwxrwxrwx    1 0        0              19 Jan 18  2006 debian -> ./pub/mirror/debian
drwxr-xr-x   10 0        0            4096 Aug 03 09:21 debian-archive
lrwxrwxrwx    1 0        0              27 Nov 30  2015 debian-backports -> pub/mirror/debian-backports
drwxr-xr-x   12 0        0            4096 Sep 29 13:13 pub
-rw-r--r--    1 0        0              26 Mar 04  2010 robots.txt
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
  u'ftp': {u'ls': u'-rw-r--r--    1 0        0              26 Mar 04  2010 robots.txt'}}]

        parsed = ftp_parse.parse(directory.splitlines())
        self.assertEqual(parsed, expected)


