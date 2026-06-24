from __future__ import unicode_literals

import unittest

from fs import filesize


class TestFilesize(unittest.TestCase):
    def test_traditional(self):

        self.assertEqual(filesize.traditional(0), "0 bytes")
        self.assertEqual(filesize.traditional(1), "1 byte")
        self.assertEqual(filesize.traditional(2), "2 bytes")
        self.assertEqual(filesize.traditional(1024), "1.0 KB")

        self.assertEqual(filesize.traditional(1024 * 1024), "1.0 MB")

        self.assertEqual(filesize.traditional(1024 * 1024 + 1), "1.0 MB")

        self.assertEqual(filesize.traditional(1.5 * 1024 * 1024), "1.5 MB")

    def test_binary(self):

        self.assertEqual(filesize.binary(0), "0 bytes")
        self.assertEqual(filesize.binary(1), "1 byte")
        self.assertEqual(filesize.binary(2), "2 bytes")
        self.assertEqual(filesize.binary(1024), "1.0 KiB")

        self.assertEqual(filesize.binary(1024 * 1024), "1.0 MiB")

        self.assertEqual(filesize.binary(1024 * 1024 + 1), "1.0 MiB")

        self.assertEqual(filesize.binary(1.5 * 1024 * 1024), "1.5 MiB")

    def test_decimal(self):

        self.assertEqual(filesize.decimal(0), "0 bytes")
        self.assertEqual(filesize.decimal(1), "1 byte")
        self.assertEqual(filesize.decimal(2), "2 bytes")
        self.assertEqual(filesize.decimal(1000), "1.0 kB")

        self.assertEqual(filesize.decimal(1000 * 1000), "1.0 MB")

        self.assertEqual(filesize.decimal(1000 * 1000 + 1), "1.0 MB")

        self.assertEqual(filesize.decimal(1200 * 1000), "1.2 MB")

    def test_rollover_decimal(self):
        # First value whose mantissa rounds up to base — the carry boundary
        self.assertEqual(filesize.decimal(999_949), "999.9 kB")
        self.assertEqual(filesize.decimal(999_950), "1.0 MB")
        # Mantissa rounds up to base — must carry to the next suffix
        self.assertEqual(filesize.decimal(999_999), "1.0 MB")
        self.assertEqual(filesize.decimal(999_999_999), "1.0 GB")
        self.assertEqual(filesize.decimal(999_999_999_999), "1.0 TB")

    def test_rollover_traditional(self):
        # First-flip carry boundary: 1,023.95 KB rounds up to 1,024.0 KB -> 1.0 MB
        self.assertEqual(filesize.traditional(1_048_524), "1,023.9 KB")
        self.assertEqual(filesize.traditional(1_048_525), "1.0 MB")
        # 1024**2 - 1 bytes is 1023.999 KB, which rounds to 1,024.0 KB
        self.assertEqual(filesize.traditional(1024**2 - 1), "1.0 MB")
        self.assertEqual(filesize.traditional(1024**3 - 1), "1.0 GB")

    def test_rollover_binary(self):
        # First-flip carry boundary: 1,023.95 KiB rounds up to 1,024.0 KiB -> 1.0 MiB
        self.assertEqual(filesize.binary(1_048_524), "1,023.9 KiB")
        self.assertEqual(filesize.binary(1_048_525), "1.0 MiB")
        self.assertEqual(filesize.binary(1024**2 - 1), "1.0 MiB")
        self.assertEqual(filesize.binary(1024**3 - 1), "1.0 GiB")

    def test_rounding_boundaries(self):
        # Within-unit rounding boundaries (no suffix change), per review on #600
        self.assertEqual(filesize.traditional(1996), "1.9 KB")
        self.assertEqual(filesize.traditional(1997), "2.0 KB")
        self.assertEqual(filesize.decimal(1950), "1.9 kB")
        self.assertEqual(filesize.decimal(1951), "2.0 kB")
        self.assertEqual(filesize.binary(1996), "1.9 KiB")
        self.assertEqual(filesize.binary(1997), "2.0 KiB")

    def test_errors(self):

        with self.assertRaises(TypeError):
            filesize.traditional("foo")
