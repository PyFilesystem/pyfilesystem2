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
            filesize.traditional(1.5 * 1024 * 1024),
            '1.5 MB'
        )

    def test_decimal(self):

        self.assertEqual(
            filesize.decimal(0),
            '0 bytes'
        )
        self.assertEqual(
            filesize.decimal(1),
            '1 byte'
        )
        self.assertEqual(
            filesize.decimal(2),
            '2 bytes'
        )
        self.assertEqual(
            filesize.decimal(1000),
            '1.0 kbit'
        )

        self.assertEqual(
            filesize.decimal(1000 * 1000),
            '1.0 Mbit'
        )

        self.assertEqual(
            filesize.decimal(1000 * 1000 + 1),
            '1.0 Mbit'
        )

        self.assertEqual(
            filesize.decimal(1200 * 1000),
            '1.2 Mbit'
        )

    def test_errors(self):

        with self.assertRaises(ValueError):
            filesize.traditional('foo')