from __future__ import unicode_literals

import multiprocessing
import unittest

from six import text_type

from fs import errors
from fs.errors import CreateFailed


class TestErrors(unittest.TestCase):
    def test_str(self):
        err = errors.FSError("oh dear")
        repr(err)
        self.assertEqual(text_type(err), "oh dear")

    def test_unsupported(self):
        err = errors.Unsupported("stuff")
        repr(err)
        self.assertEqual(text_type(err), "not supported")

    def test_raise_in_multiprocessing(self):
        # Without the __reduce__ methods in FSError subclasses, this test will hang forever.
        tests = [
            [errors.ResourceNotFound, "some_path"],
            [errors.FilesystemClosed],
            [errors.CreateFailed],
            [errors.NoSysPath, "some_path"],
            [errors.NoURL, "some_path", "some_purpose"],
            [errors.Unsupported],
            [errors.IllegalBackReference, "path"],
            [errors.MissingInfoNamespace, "path"],
        ]
        try:
            pool = multiprocessing.Pool(1)
            for args in tests:
                exc = args[0](*args[1:])
                exc.__reduce__()
                with self.assertRaises(args[0]):
                    pool.apply(_multiprocessing_test_task, args)
        finally:
            pool.close()


def _multiprocessing_test_task(err, *args):
    raise err(*args)


class TestCreateFailed(unittest.TestCase):
    def test_catch_all(self):

        errors = (ZeroDivisionError, ValueError, CreateFailed)

        @CreateFailed.catch_all
        def test(x):
            raise errors[x]

        for index, _exc in enumerate(errors):
            try:
                test(index)
            except Exception as e:
                self.assertIsInstance(e, CreateFailed)
                if e.exc is not None:
                    self.assertNotIsInstance(e.exc, CreateFailed)
