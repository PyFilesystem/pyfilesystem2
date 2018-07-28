import os

from fs import enums

import unittest


class TestEnums(unittest.TestCase):
    def test_enums(self):
        self.assertEqual(enums.Seek.current, os.SEEK_CUR)
        self.assertEqual(enums.Seek.end, os.SEEK_END)
        self.assertEqual(enums.Seek.set, os.SEEK_SET)
        self.assertEqual(enums.ResourceType.unknown, 0)
