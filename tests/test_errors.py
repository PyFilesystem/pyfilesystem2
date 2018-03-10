from __future__ import unicode_literals

import unittest

from six import text_type

from fs import errors
from fs.errors import CreateFailed


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


class TestCreateFailed(unittest.TestCase):

    def test_catch_all(self):

        errors = (ZeroDivisionError, ValueError, CreateFailed)

        @CreateFailed.catch_all
        def test(x):
            raise errors[x]

        for index, exc in enumerate(errors):
            try:
                test(index)
            except Exception as e:
                self.assertIsInstance(e, CreateFailed)
                if e.exc is not None:
                    self.assertNotIsInstance(e.exc, CreateFailed)
