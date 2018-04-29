from fs import enums

import unittest


class TestEnums(unittest.TestCase):

    def test_enums(self):
        self.assertEqual(enums.Seek.current, 0)
        self.assertEqual(enums.Seek.end, 1)
        self.assertEqual(enums.Seek.set, 2)
        self.assertEqual(enums.ResourceType.unknown, 0)
