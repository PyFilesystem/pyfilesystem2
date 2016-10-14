from __future__ import unicode_literals

import unittest

from fs import lrucache


class TestLRUCache(unittest.TestCase):

    def setUp(self):
        self.lrucache = lrucache.LRUCache(3)

    def test_lrucache(self):
        # insert some values
        self.lrucache['foo'] = 1
        self.lrucache['bar'] = 2
        self.lrucache['baz'] = 3
        self.assertIn('foo', self.lrucache)

        #  Cache size is 3, so the following should kick oldest one out
        self.lrucache['egg'] = 4
        self.assertNotIn('foo', self.lrucache)
        self.assertIn('egg', self.lrucache)

        # cache is now full
        # look up two keys
        self.lrucache['bar']
        self.lrucache['baz']

        # Insert a new value
        self.lrucache['eggegg'] = 5
        # Check it kicked out the 'oldest' key
        self.assertNotIn('egg', self.lrucache)
