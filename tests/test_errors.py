from __future__ import unicode_literals

import unittest

from six import text_type

from fs import errors


class TestErrors(unittest.TestCase):

    def test_str(self):
        err = errors.FSError('oh dear')
        repr(err)
        self.assertEqual(
            text_type(err),
            'oh dear'
        )

    def test_unsupported(self):
        err = errors.Unsupported('stuff')
        repr(err)
        self.assertEqual(
            text_type(err),
            "not supported"
        )
