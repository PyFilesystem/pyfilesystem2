from __future__ import unicode_literals

import unittest
import warnings


from fs.base import _new_name


class TestNewNameDecorator(unittest.TestCase):
    def times_two(n):
        return n * 2

    double = _new_name(times_two, "double")

    def test_old_name(self):
        """Test _new_name method issues a warning"""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = self.times_2(2)
            self.assertEqual(len(w), 1)
            self.assertEqual(w[0].category, DeprecationWarning)
            self.assertEqual(
                w[0].message,
                "method 'times_two' has been deprecated, please renamed to 'double'",
            )
        self.assertEqual(result, 2)
