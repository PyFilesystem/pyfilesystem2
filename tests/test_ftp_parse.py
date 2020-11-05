from __future__ import unicode_literals

import time
import unittest

from fs import _ftp_parse as ftp_parse

try:
    from unittest import mock
except ImportError:
    import mock

time2017 = time.struct_time([2017, 11, 28, 1, 1, 1, 1, 332, 0])


class TestFTPParse(unittest.TestCase):
    @mock.patch("time.localtime")
    def test_parse_time(self, mock_localtime):
        self.assertEqual(
            ftp_parse._parse_time("JUL 05 1974", formats=["%b %d %Y"]), 142214400.0
        )

        mock_localtime.return_value = time2017
        self.assertEqual(
            ftp_parse._parse_time("JUL 05 02:00", formats=["%b %d %H:%M"]), 1499220000.0
        )

        self.assertEqual(
            ftp_parse._parse_time("05-07-17  02:00AM", formats=["%d-%m-%y %I:%M%p"]),
            1499220000.0,
        )

        self.assertEqual(ftp_parse._parse_time("notadate", formats=["%b %d %Y"]), None)

    def test_parse(self):
        self.assertEqual(ftp_parse.parse([""]), [])

    def test_parse_line(self):
        self.assertIs(ftp_parse.parse_line("not a dir"), None)

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

        expected = [
            {
                "access": {
                    "group": "0",
                    "permissions": [
                        "g_r",
                        "g_w",
                        "g_x",
                        "o_r",
                        "o_w",
                        "o_x",
                        "u_r",
                        "u_w",
                        "u_x",
                    ],
                    "user": "0",
                },
                "basic": {"is_dir": True, "name": "debian"},
                "details": {"modified": 1137542400.0, "size": 19, "type": 1},
                "ftp": {
                    "ls": "lrwxrwxrwx    1 0        0              19 Jan 18  2006 debian -> ./pub/mirror/debian"
                },
            },
            {
                "access": {
                    "group": "0",
                    "permissions": ["g_r", "g_x", "o_r", "o_x", "u_r", "u_w", "u_x"],
                    "user": "0",
                },
                "basic": {"is_dir": True, "name": "debian-archive"},
                "details": {"modified": 1501752060.0, "size": 4096, "type": 1},
                "ftp": {
                    "ls": "drwxr-xr-x   10 0        0            4096 Aug 03 09:21 debian-archive"
                },
            },
            {
                "access": {
                    "group": "0",
                    "permissions": [
                        "g_r",
                        "g_w",
                        "g_x",
                        "o_r",
                        "o_w",
                        "o_x",
                        "u_r",
                        "u_w",
                        "u_x",
                    ],
                    "user": "0",
                },
                "basic": {"is_dir": True, "name": "debian-backports"},
                "details": {"modified": 1448841600.0, "size": 27, "type": 1},
                "ftp": {
                    "ls": "lrwxrwxrwx    1 0        0              27 Nov 30  2015 debian-backports -> pub/mirror/debian-backports"
                },
            },
            {
                "access": {
                    "group": "0",
                    "permissions": ["g_r", "g_x", "o_r", "o_x", "u_r", "u_w", "u_x"],
                    "user": "0",
                },
                "basic": {"is_dir": True, "name": "pub"},
                "details": {"modified": 1506690780.0, "size": 4096, "type": 1},
                "ftp": {
                    "ls": "drwxr-xr-x   12 0        0            4096 Sep 29 13:13 pub"
                },
            },
            {
                "access": {
                    "group": "0",
                    "permissions": ["g_r", "o_r", "u_r", "u_w"],
                    "user": "0",
                },
                "basic": {"is_dir": False, "name": "robots.txt"},
                "details": {"modified": 1267660800.0, "size": 26, "type": 2},
                "ftp": {
                    "ls": "-rw-r--r--    1 0        0              26 Mar 04  2010 robots.txt"
                },
            },
            {
                "access": {
                    "group": "bar",
                    "permissions": ["g_r", "g_x", "o_r", "o_x", "u_r", "u_w", "u_x"],
                    "user": "foo",
                },
                "basic": {"is_dir": True, "name": "test"},
                "details": {"modified": 1507107900.0, "size": 4096, "type": 1},
                "ftp": {
                    "ls": "drwxr-xr-x   8 foo      bar          4096 Oct  4 09:05 test"
                },
            },
            {
                "access": {
                    "group": "foo-group",
                    "permissions": ["g_r", "g_x", "o_r", "o_x", "u_r", "u_w", "u_x"],
                    "user": "foo-user",
                },
                "basic": {"is_dir": True, "name": "240485"},
                "details": {"modified": 1483617540.0, "size": 0, "type": 1},
                "ftp": {
                    "ls": "drwxr-xr-x   2 foo-user foo-group         0 Jan  5 11:59 240485"
                },
            },
        ]

        parsed = ftp_parse.parse(directory.splitlines())
        self.assertEqual(parsed, expected)

    @mock.patch("time.localtime")
    def test_decode_windowsnt(self, mock_localtime):
        mock_localtime.return_value = time2017
        directory = """\
unparsable line
11-02-17  02:00AM       <DIR>          docs
11-02-17  02:12PM       <DIR>          images
11-02-17 02:12PM <DIR> AM to PM
11-02-17  03:33PM                 9276 logo.gif
05-11-20   22:11  <DIR>       src
11-02-17   01:23       1      12
11-02-17    4:54                 0 icon.bmp
11-02-17    4:54AM                 0 icon.gif
11-02-17    4:54PM                 0 icon.png
11-02-17    16:54                 0 icon.jpg
"""
        expected = [
            {
                "basic": {"is_dir": True, "name": "docs"},
                "details": {"modified": 1486778400.0, "type": 1},
                "ftp": {"ls": "11-02-17  02:00AM       <DIR>          docs"},
            },
            {
                "basic": {"is_dir": True, "name": "images"},
                "details": {"modified": 1486822320.0, "type": 1},
                "ftp": {"ls": "11-02-17  02:12PM       <DIR>          images"},
            },
            {
                "basic": {"is_dir": True, "name": "AM to PM"},
                "details": {"modified": 1486822320.0, "type": 1},
                "ftp": {"ls": "11-02-17 02:12PM <DIR> AM to PM"},
            },
            {
                "basic": {"is_dir": False, "name": "logo.gif"},
                "details": {"modified": 1486827180.0, "size": 9276, "type": 2},
                "ftp": {"ls": "11-02-17  03:33PM                 9276 logo.gif"},
            },
            {
                "basic": {"is_dir": True, "name": "src"},
                "details": {"modified": 1604614260.0, "type": 1},
                "ftp": {"ls": "05-11-20   22:11  <DIR>       src"},
            },
            {
                "basic": {"is_dir": False, "name": "12"},
                "details": {"modified": 1486776180.0, "size": 1, "type": 2},
                "ftp": {"ls": "11-02-17   01:23       1      12"},
            },
            {
                "basic": {"is_dir": False, "name": "icon.bmp"},
                "details": {"modified": 1486788840.0, "size": 0, "type": 2},
                "ftp": {"ls": "11-02-17    4:54                 0 icon.bmp"},
            },
            {
                "basic": {"is_dir": False, "name": "icon.gif"},
                "details": {"modified": 1486788840.0, "size": 0, "type": 2},
                "ftp": {"ls": "11-02-17    4:54AM                 0 icon.gif"},
            },
            {
                "basic": {"is_dir": False, "name": "icon.png"},
                "details": {"modified": 1486832040.0, "size": 0, "type": 2},
                "ftp": {"ls": "11-02-17    4:54PM                 0 icon.png"},
            },
            {
                "basic": {"is_dir": False, "name": "icon.jpg"},
                "details": {"modified": 1486832040.0, "size": 0, "type": 2},
                "ftp": {"ls": "11-02-17    16:54                 0 icon.jpg"},
            },
        ]

        parsed = ftp_parse.parse(directory.splitlines())
        self.assertEqual(parsed, expected)
