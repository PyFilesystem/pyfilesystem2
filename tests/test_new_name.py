from __future__ import unicode_literals

import unittest
import warnings


from fs.base import _new_name


class TestNewNameDecorator(unittest.TestCase):
    def double(self, n):
        "Double a number"
        return n * 2

    times_2 = _new_name(double, "times_2")

    def test_old_name(self):
        """Test _new_name method issues a warning"""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = self.times_2(2)
            self.assertEqual(len(w), 1)
            self.assertEqual(w[0].category, DeprecationWarning)
            self.assertEqual(
                str(w[0].message),
                "method 'times_2' has been deprecated, please rename to 'double'",
            )
        self.assertEqual(result, 4)
