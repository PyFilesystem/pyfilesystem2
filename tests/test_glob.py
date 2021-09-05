from __future__ import unicode_literals

import re
import unittest

from parameterized import parameterized

from fs import glob, open_fs


class TestGlob(unittest.TestCase):
    def setUp(self):
        fs = self.fs = open_fs("mem://")
        fs.writetext("foo.py", "Hello, World")
        fs.touch("bar.py")
        fs.touch("baz.py")
        fs.makedirs("egg")
        fs.writetext("egg/foo.py", "from fs import open_fs")
        fs.touch("egg/foo.pyc")
        fs.makedirs("a/b/c/").writetext("foo.py", "import fs")
        repr(fs.glob)

    @parameterized.expand(
        [
            ("*.?y", "/test.py", True),
            ("*.py", "/test.py", True),
            ("*.py", "__init__.py", True),
            ("*.py", "/test.pc", False),
            ("*.py", "/foo/test.py", False),
            ("foo/*.py", "/foo/test.py", True),
            ("foo/*.py", "/bar/foo/test.py", False),
            ("?oo/*.py", "/foo/test.py", True),
            ("*/*.py", "/foo/test.py", True),
            ("foo/*.py", "/bar/foo/test.py", False),
            ("/foo/**", "/foo/test.py", True),
            ("**/foo/*.py", "/bar/foo/test.py", True),
            ("foo/**/bar/*.py", "/foo/bar/test.py", True),
            ("foo/**/bar/*.py", "/foo/baz/egg/bar/test.py", True),
            ("foo/**/bar/*.py", "/foo/baz/egg/bar/egg/test.py", False),
            ("**", "/test.py", True),
            ("/**", "/test.py", True),
            ("**", "/test", True),
            ("**", "/test/", True),
            ("**/", "/test/", True),
            ("**/", "/test.py", False),
        ]
    )
    def test_match(self, pattern, path, expected):
        self.assertEqual(glob.match(pattern, path), expected, msg=(pattern, path))
        # Run a second time to test cache
        self.assertEqual(glob.match(pattern, path), expected, msg=(pattern, path))

    def test_count_1dir(self):
        globber = glob.BoundGlobber(self.fs)
        counts = globber("*.py").count()
        self.assertEqual(counts, glob.Counts(files=3, directories=0, data=12))
        repr(globber("*.py"))

    def test_count_2dir(self):
        globber = glob.BoundGlobber(self.fs)
        counts = globber("*/*.py").count()
        self.assertEqual(counts, glob.Counts(files=1, directories=0, data=22))

    def test_count_recurse_dir(self):
        globber = glob.BoundGlobber(self.fs)
        counts = globber("**/*.py").count()
        self.assertEqual(counts, glob.Counts(files=5, directories=0, data=43))

    def test_count_lines(self):
        globber = glob.BoundGlobber(self.fs)
        line_counts = globber("**/*.py").count_lines()
        self.assertEqual(line_counts, glob.LineCounts(lines=3, non_blank=3))

    def test_count_dirs(self):
        globber = glob.BoundGlobber(self.fs)
        counts = globber("**/?/").count()
        self.assertEqual(counts, glob.Counts(files=0, directories=3, data=0))

    def test_count_all(self):
        globber = glob.BoundGlobber(self.fs)
        counts = globber("**").count()
        self.assertEqual(counts, glob.Counts(files=6, directories=4, data=43))
        counts = globber("**/").count()
        self.assertEqual(counts, glob.Counts(files=0, directories=4, data=0))

    def test_remove(self):
        globber = glob.BoundGlobber(self.fs)
        self.assertTrue(self.fs.exists("egg/foo.pyc"))
        removed_count = globber("**/*.pyc").remove()
        self.assertEqual(removed_count, 1)
        self.assertFalse(self.fs.exists("egg/foo.pyc"))

    def test_remove_dir(self):
        globber = glob.BoundGlobber(self.fs)
        self.assertTrue(self.fs.exists("egg/foo.pyc"))
        removed_count = globber("**/?/").remove()
        self.assertEqual(removed_count, 3)
        self.assertFalse(self.fs.exists("a"))
        self.assertTrue(self.fs.exists("egg"))

    def test_remove_all(self):
        globber = glob.BoundGlobber(self.fs)
        globber("**").remove()
        self.assertEqual(sorted(self.fs.listdir("/")), [])

    translate_test_cases = [
            ("foo.py", ["foo.py"], ["Foo.py", "foo_py", "foo", ".py"]),
            ("foo?py", ["foo.py", "fooapy"], ["foo/py", "foopy", "fopy"]),
            ("bar/foo.py", ["bar/foo.py"], []),
            ("bar?foo.py", ["barafoo.py"], ["bar/foo.py"]),
            ("???.py", ["foo.py", "bar.py", "FOO.py"], [".py", "foo.PY"]),
            ("bar/*.py", ["bar/.py", "bar/foo.py"], ["bar/foo"]),
            ("bar/foo*.py", ["bar/foo.py", "bar/foobaz.py"], ["bar/foo", "bar/.py"]),
            ("*/[bar]/foo.py", ["/b/foo.py", "x/a/foo.py", "/r/foo.py"], ["b/foo.py", "/bar/foo.py"]),
            ("[!bar]/foo.py", ["x/foo.py"], ["//foo.py"]),
            ("[.py", ["[.py"], [".py", "."]),
        ]

    @parameterized.expand(translate_test_cases)
    def test_translate(self, glob_pattern, expected_matches, expected_not_matches):
        translated = glob._translate(glob_pattern)
        for m in expected_matches:
            self.assertTrue(re.match(translated, m))
        for m in expected_not_matches:
            self.assertFalse(re.match(translated, m))

    @parameterized.expand(translate_test_cases)
    def test_translate_glob_simple(self, glob_pattern, expected_matches, expected_not_matches):
        levels, translated = glob._translate_glob(glob_pattern)
        self.assertEqual(levels, glob_pattern.count("/") + 1)
        for m in expected_matches:
            self.assertTrue(re.match(translated, "/" + m))
        for m in expected_not_matches:
            self.assertFalse(re.match(translated, m))
            self.assertFalse(re.match(translated, "/" + m))

    @parameterized.expand(
        [
            ("foo/**/bar", ["/foo/bar", "/foo/baz/bar", "/foo/baz/qux/bar"], ["/foo"]),
            ("**/*/bar", ["/foo/bar", "/foo/bar"], ["/bar", "/bar"]),
            ("/**/foo/**/bar", ["/baz/foo/qux/bar", "/foo/bar"], ["/bar"]),
        ]
    )
    def test_translate_glob(self, glob_pattern, expected_matches, expected_not_matches):
        levels, translated = glob._translate_glob(glob_pattern)
        self.assertIsNone(levels)
        for m in expected_matches:
            self.assertTrue(re.match(translated, m))
        for m in expected_not_matches:
            self.assertFalse(re.match(translated, m))
