from __future__ import unicode_literals

import unittest

from fs import mode


class TestMode(unittest.TestCase):

    def test_checks(self):
        self.assertTrue(mode.check_readable('r'))
        self.assertTrue(mode.check_readable('r+'))
        self.assertTrue(mode.check_readable('rt'))
        self.assertTrue(mode.check_readable('rb'))

        self.assertFalse(mode.check_readable('w'))
        self.assertTrue(mode.check_readable('w+'))
        self.assertFalse(mode.check_readable('wt'))
        self.assertFalse(mode.check_readable('wb'))
        self.assertFalse(mode.check_readable('a'))

        self.assertTrue(mode.check_writable('w'))
        self.assertTrue(mode.check_writable('w+'))
        self.assertTrue(mode.check_writable('r+'))
        self.assertFalse(mode.check_writable('r'))
        self.assertTrue(mode.check_writable('a'))
