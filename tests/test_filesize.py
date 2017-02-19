from __future__ import unicode_literals

from fs import filesize

import unittest


class TestFilesize(unittest.TestCase):

    def test_traditional(self):

        self.assertEqual(
            filesize.traditional(0),
            '0 bytes'
        )
        self.assertEqual(
            filesize.traditional(1),
            '1 byte'
        )
        self.assertEqual(
            filesize.traditional(2),
            '2 bytes'
        )
        self.assertEqual(
            filesize.traditional(1024),
            '1.0 KB'
        )

        self.assertEqual(
            filesize.traditional(1024 * 1024),
            '1.0 MB'
        )

        self.assertEqual(
            filesize.traditional(1024 * 1024 + 1),
            '1.0 MB'
        )

        self.assertEqual(
            filesize.traditional(1024 * 1024 + 65536),
            '1.0 MB'
        )

    def test_decimal(self):

        self.assertEqual(
            filesize.traditional(0),
            '0 bytes'
        )
        self.assertEqual(
            filesize.traditional(1),
            '1 byte'
        )
        self.assertEqual(
            filesize.traditional(2),
            '2 bytes'
        )
        self.assertEqual(
            filesize.traditional(1024),
            '1.0 KB'
        )

        self.assertEqual(
            filesize.traditional(1024 * 1024),
            '1.0 MB'
        )

        self.assertEqual(
            filesize.traditional(1024 * 1024 + 1),
            '1.0 MB'
        )

        self.assertEqual(
            filesize.traditional(1024 * 1024 + 65536),
            '1.0 MB'
        )

    def test_errors(self):

        with self.assertRaises(ValueError):
            filesize.traditional('foo')