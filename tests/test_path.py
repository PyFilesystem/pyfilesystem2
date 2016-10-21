from __future__ import unicode_literals, print_function

"""
  fstests.test_path:  testcases for the fs path functions

"""


import unittest

from fs.path import *


class TestPathFunctions(unittest.TestCase):
    """Testcases for FS path functions."""

    def test_normpath(self):
        tests = [
            ("\\a\\b\\c", "\\a\\b\\c"),
            (".", ""),
            ("./", ""),
            ("", ""),
            ("/.", "/"),
            ("/a/b/c", "/a/b/c"),
            ("a/b/c", "a/b/c"),
            ("a/b/../c/", "a/c"),
            ("/", "/"),
            ("a/\N{GREEK SMALL LETTER BETA}/c", "a/\N{GREEK SMALL LETTER BETA}/c"),
        ]
        for path, result in tests:
            self.assertEqual(normpath(path), result)

    def test_pathjoin(self):
        tests = [
            ("", "a", "a"),
            ("a", "a", "a/a"),
            ("a/b", "../c", "a/c"),
            ("a/b/../c", "d", "a/c/d"),
            ("/a/b/c", "d", "/a/b/c/d"),
            ("/a/b/c", "../../../d", "/d"),
            ("a", "b", "c", "a/b/c"),
            ("a/b/c", "../d", "c", "a/b/d/c"),
            ("a/b/c", "../d", "/a", "/a"),
            ("aaa", "bbb/ccc", "aaa/bbb/ccc"),
            ("aaa", "bbb\\ccc", "aaa/bbb\\ccc"),
            ("aaa", "bbb", "ccc", "/aaa", "eee", "/aaa/eee"),
            ("a/b", "./d", "e", "a/b/d/e"),
            ("/", "/", "/"),
            ("/", "", "/"),
            (u"a/\N{GREEK SMALL LETTER BETA}", "c", u"a/\N{GREEK SMALL LETTER BETA}/c"),
        ]
        for testpaths in tests:
            paths = testpaths[:-1]
            result = testpaths[-1]
            self.assertEqual(join(*paths), result)

        self.assertRaises(ValueError, join, "..")
        self.assertRaises(ValueError, join, "../")
        self.assertRaises(ValueError, join, "/..")
        self.assertRaises(ValueError, join, "./../")
        self.assertRaises(ValueError, join, "a/b", "../../..")
        self.assertRaises(ValueError, join, "a/b/../../../d")

    def test_relpath(self):
        tests = [
            ("/a/b", "a/b"),
            ("a/b", "a/b"),
            ("/", "")
        ]
        for path, result in tests:
            self.assertEqual(relpath(path), result)

    def test_abspath(self):
        tests = [
            ("/a/b", "/a/b"),
            ("a/b", "/a/b"),
            ("/", "/")
        ]
        for path, result in tests:
            self.assertEqual(abspath(path), result)

    def test_forcedir(self):
        self.assertEqual(forcedir('foo'), 'foo/')
        self.assertEqual(forcedir('foo/'), 'foo/')

    def test_frombase(self):
        with self.assertRaises(ValueError):
            frombase('foo', 'bar/baz')
        self.assertEqual(frombase('foo', 'foo/bar'), '/bar')

    def test_isabs(self):
        self.assertTrue(isabs('/'))
        self.assertTrue(isabs('/foo'))
        self.assertFalse(isabs('foo'))

    def test_iteratepath(self):
        tests = [
            ("a/b", ["a", "b"]),
            ("", []),
            ("aaa/bbb/ccc", ["aaa", "bbb", "ccc"]),
            ("a/b/c/../d", ["a", "b", "d"])
        ]

        for path, results in tests:
            for path_component, expected in zip(iteratepath(path), results):
                self.assertEqual(path_component, expected)

    def test_combine(self):
        self.assertEqual(combine('', 'bar'), 'bar')
        self.assertEqual(combine('foo', 'bar'), 'foo/bar')

    def test_pathsplit(self):
        tests = [
            ("a/b", ("a", "b")),
            ("a/b/c", ("a/b", "c")),
            ("a", ("", "a")),
            ("", ("", "")),
            ("/", ("/", "")),
            ("/foo", ("/", "foo")),
            ("foo/bar", ("foo", "bar")),
            ("foo/bar/baz", ("foo/bar", "baz")),
        ]
        for path, result in tests:
            self.assertEqual(split(path), result)

    def test_splitext(self):
        self.assertEqual(splitext('foo.bar'), ('foo', '.bar'))
        self.assertEqual(splitext('foo.bar.baz'), ('foo.bar', '.baz'))
        self.assertEqual(splitext('foo'), ('foo', ''))

    def test_recursepath(self):
        self.assertEquals(recursepath("/"), ["/"])
        self.assertEquals(recursepath("hello"), ["/", "/hello"])
        self.assertEquals(recursepath("/hello/world/"), ["/", "/hello", "/hello/world"])
        self.assertEquals(recursepath("/hello/world/", reverse=True),
                          ["/hello/world", "/hello", "/"])
        self.assertEquals(recursepath("hello", reverse=True), ["/hello", "/"])
        self.assertEquals(recursepath("", reverse=True), ["/"])

    def test_isbase(self):
        self.assertTrue(isbase('foo/bar', 'foo'))
        self.assertFalse(isbase('foo/bar', 'baz'))

    def test_isparent(self):
        self.assertTrue(isparent("foo/bar", "foo/bar/spam.txt"))
        self.assertTrue(isparent("foo/bar/", "foo/bar"))
        self.assertFalse(isparent("foo/barry", "foo/baz/bar"))
        self.assertFalse(isparent("foo/bar/baz/", "foo/baz/bar"))
        self.assertFalse(isparent("foo/var/baz/egg", "foo/baz/bar"))

    def test_issamedir(self):
        self.assertTrue(issamedir("foo/bar/baz.txt", "foo/bar/spam.txt"))
        self.assertFalse(issamedir("foo/bar/baz/txt", "spam/eggs/spam.txt"))

    def test_isdotfile(self):
        for path in ['.foo',
                     '.svn',
                     'foo/.svn',
                     'foo/bar/.svn',
                     '/foo/.bar']:
            self.assert_(isdotfile(path))

        for path in ['asfoo',
                     'df.svn',
                     'foo/er.svn',
                     'foo/bar/test.txt',
                     '/foo/bar']:
            self.assertFalse(isdotfile(path))

    def test_dirname(self):
        tests = [('foo', ''),
                 ('foo/bar', 'foo'),
                 ('foo/bar/baz', 'foo/bar'),
                 ('/foo/bar', '/foo'),
                 ('/foo', '/'),
                 ('/', '/')]
        for path, test_dirname in tests:
            self.assertEqual(dirname(path), test_dirname)

    def test_basename(self):
        tests = [('foo', 'foo'),
                 ('foo/bar', 'bar'),
                 ('foo/bar/baz', 'baz'),
                 ('/', '')]
        for path, test_basename in tests:
            self.assertEqual(basename(path), test_basename)

    def test_iswildcard(self):
        self.assert_(iswildcard('*'))
        self.assert_(iswildcard('*.jpg'))
        self.assert_(iswildcard('foo/*'))
        self.assert_(iswildcard('foo/{}'))
        self.assertFalse(iswildcard('foo'))
        self.assertFalse(iswildcard('img.jpg'))
        self.assertFalse(iswildcard('foo/bar'))

    def test_realtivefrom(self):
        tests = [('/', '/foo.html', 'foo.html'),
                 ('/foo', '/foo/bar.html', 'bar.html'),
                 ('/foo/bar/', '/egg.html', '../../egg.html'),
                 ('/a/b/c/d', 'e', '../../../../e'),
                 ('/a/b/c/d', 'a/d', '../../../d'),
                 ('/docs/', 'tags/index.html', '../tags/index.html'),
                 ('foo/bar', 'baz/index.html', '../../baz/index.html'),
                 ('', 'a', 'a'),
                 ('a', 'b/c', '../b/c')
                 ]

        for base, path, result in tests:
            self.assertEqual(relativefrom(base, path), result)
