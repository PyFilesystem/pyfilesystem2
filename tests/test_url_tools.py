# coding: utf-8
"""Test url tools. """
from __future__ import unicode_literals

import platform
import unittest

from fs._url_tools import url_quote


class TestBase(unittest.TestCase):
    def test_quote(self):
        test_fixtures = [
            # test_snippet, expected
            ["foo/bar/egg/foofoo", "foo/bar/egg/foofoo"],
            ["foo/bar ha/barz", "foo/bar%20ha/barz"],
            ["example b.txt", "example%20b.txt"],
            ["exampleㄓ.txt", "example%E3%84%93.txt"],
        ]
        if platform.system() == "Windows":
            test_fixtures.extend(
                [
                    ["C:\\My Documents\\test.txt", "C:/My%20Documents/test.txt"],
                    ["C:/My Documents/test.txt", "C:/My%20Documents/test.txt"],
                    # on Windows '\' is regarded as path separator
                    ["test/forward\\slash", "test/forward/slash"],
                ]
            )
        else:
            test_fixtures.extend(
                [
                    # colon:tmp is bad path under Windows
                    ["test/colon:tmp", "test/colon%3Atmp"],
                    # Unix treat \ as %5C
                    ["test/forward\\slash", "test/forward%5Cslash"],
                ]
            )
        for test_snippet, expected in test_fixtures:
            self.assertEqual(url_quote(test_snippet), expected)
