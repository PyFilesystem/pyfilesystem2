from __future__ import unicode_literals

import unittest

from six import text_type

from fs.mode import check_readable, check_writable, Mode


class TestMode(unittest.TestCase):

    def test_checks(self):
        self.assertTrue(check_readable('r'))
        self.assertTrue(check_readable('r+'))
        self.assertTrue(check_readable('rt'))
        self.assertTrue(check_readable('rb'))

        self.assertFalse(check_readable('w'))
        self.assertTrue(check_readable('w+'))
        self.assertFalse(check_readable('wt'))
        self.assertFalse(check_readable('wb'))
        self.assertFalse(check_readable('a'))

        self.assertTrue(check_writable('w'))
        self.assertTrue(check_writable('w+'))
        self.assertTrue(check_writable('r+'))
        self.assertFalse(check_writable('r'))
        self.assertTrue(check_writable('a'))

    def test_mode_object(self):
        with self.assertRaises(ValueError):
            Mode('')
        with self.assertRaises(ValueError):
            Mode('J')
        with self.assertRaises(ValueError):
            Mode('b')
        with self.assertRaises(ValueError):
            Mode('rtb')

        mode = Mode('w')
        repr(mode)
        self.assertEqual(text_type(mode), 'w')
        self.assertTrue(mode.create)
        self.assertFalse(mode.reading)
        self.assertTrue(mode.writing)
        self.assertFalse(mode.appending)
        self.assertFalse(mode.updating)
        self.assertTrue(mode.truncate)
        self.assertFalse(mode.exclusive)
        self.assertFalse(mode.binary)
        self.assertTrue(mode.text)
