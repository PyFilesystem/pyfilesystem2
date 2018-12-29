from __future__ import unicode_literals

import unittest

from fs import glob
from fs import open_fs


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

    def test_match(self):
        tests = [
            ("*.?y", "/test.py", True),
            ("*.py", "/test.py", True),
            ("*.py", "/test.pc", False),
            ("*.py", "/foo/test.py", False),
            ("foo/*.py", "/foo/test.py", True),
            ("foo/*.py", "/bar/foo/test.py", False),
            ("?oo/*.py", "/foo/test.py", True),
            ("*/*.py", "/foo/test.py", True),
            ("foo/*.py", "/bar/foo/test.py", False),
            ("**/foo/*.py", "/bar/foo/test.py", True),
            ("foo/**/bar/*.py", "/foo/bar/test.py", True),
            ("foo/**/bar/*.py", "/foo/baz/egg/bar/test.py", True),
            ("foo/**/bar/*.py", "/foo/baz/egg/bar/egg/test.py", False),
            ("**", "/test.py", True),
            ("**", "/test", True),
            ("**", "/test/", True),
            ("**/", "/test/", True),
            ("**/", "/test.py", False),
        ]
        for pattern, path, expected in tests:
            self.assertEqual(glob.match(pattern, path), expected)
        # Run a second time to test cache
        for pattern, path, expected in tests:
            self.assertEqual(glob.match(pattern, path), expected)

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
