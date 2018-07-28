from __future__ import unicode_literals
from __future__ import print_function

import unittest

from six import text_type

from fs.permissions import make_mode, Permissions


class TestPermissions(unittest.TestCase):
    def test_make_mode(self):
        self.assertEqual(make_mode(None), 0o777)
        self.assertEqual(make_mode(0o755), 0o755)
        self.assertEqual(make_mode(["u_r", "u_w", "u_x"]), 0o700)
        self.assertEqual(make_mode(Permissions(user="rwx")), 0o700)

    def test_parse(self):
        self.assertEqual(Permissions.parse("---------").mode, 0)
        self.assertEqual(Permissions.parse("rwxrw-r--").mode, 0o764)

    def test_create(self):
        self.assertEqual(Permissions.create(None).mode, 0o777)
        self.assertEqual(Permissions.create(0o755).mode, 0o755)
        self.assertEqual(Permissions.create(["u_r", "u_w", "u_x"]).mode, 0o700)
        self.assertEqual(Permissions.create(Permissions(user="rwx")).mode, 0o700)
        with self.assertRaises(ValueError):
            Permissions.create("foo")

    def test_constructor(self):
        p = Permissions(names=["foo", "bar"])
        self.assertIn("foo", p)
        self.assertIn("bar", p)
        self.assertNotIn("baz", p)

        p = Permissions(user="r", group="w", other="x")
        self.assertIn("u_r", p)
        self.assertIn("g_w", p)
        self.assertIn("o_x", p)
        self.assertNotIn("sticky", p)
        self.assertNotIn("setuid", p)
        self.assertNotIn("setguid", p)

        p = Permissions(
            user="rwx", group="rwx", other="rwx", sticky=True, setuid=True, setguid=True
        )
        self.assertIn("sticky", p)
        self.assertIn("setuid", p)
        self.assertIn("setguid", p)

        p = Permissions(mode=0o421)
        self.assertIn("u_r", p)
        self.assertIn("g_w", p)
        self.assertIn("o_x", p)
        self.assertNotIn("u_w", p)
        self.assertNotIn("g_x", p)
        self.assertNotIn("o_r", p)
        self.assertNotIn("sticky", p)
        self.assertNotIn("setuid", p)
        self.assertNotIn("setguid", p)

    def test_properties(self):
        p = Permissions()
        self.assertFalse(p.u_r)
        self.assertNotIn("u_r", p)
        p.u_r = True
        self.assertIn("u_r", p)
        self.assertTrue(p.u_r)
        p.u_r = False
        self.assertNotIn("u_r", p)
        self.assertFalse(p.u_r)

        self.assertFalse(p.u_w)
        p.add("u_w")
        self.assertTrue(p.u_w)
        p.remove("u_w")
        self.assertFalse(p.u_w)

    def test_repr(self):
        self.assertEqual(
            repr(Permissions()), "Permissions(user='', group='', other='')"
        )
        self.assertEqual(repr(Permissions(names=["foo"])), "Permissions(names=['foo'])")
        repr(Permissions(user="rwx", group="rw", other="r"))
        repr(Permissions(user="rwx", group="rw", other="r", sticky=True))
        repr(Permissions(user="rwx", group="rw", other="r", setuid=True))
        repr(Permissions(user="rwx", group="rw", other="r", setguid=True))

    def test_as_str(self):
        p = Permissions(user="rwx", group="rwx", other="rwx")
        self.assertEqual(p.as_str(), "rwxrwxrwx")
        self.assertEqual(str(p), "rwxrwxrwx")
        p = Permissions(mode=0o777, setuid=True, setguid=True, sticky=True)
        self.assertEqual(p.as_str(), "rwsrwsrwt")

    def test_mode(self):
        p = Permissions(user="rwx", group="rw", other="")
        self.assertEqual(p.mode, 0o760)

    def test_serialize(self):
        p = Permissions(names=["foo"])
        self.assertEqual(p.dump(), ["foo"])
        pp = Permissions.load(["foo"])
        self.assertIn("foo", pp)

    def test_iter(self):
        iter_p = iter(Permissions(names=["foo"]))
        self.assertEqual(list(iter_p), ["foo"])

    def test_equality(self):
        self.assertEqual(Permissions(mode=0o700), Permissions(user="rwx"))
        self.assertNotEqual(Permissions(mode=0o500), Permissions(user="rwx"))

        self.assertEqual(Permissions(mode=0o700), ["u_r", "u_w", "u_x"])

    def test_copy(self):
        p = Permissions(mode=0o700)
        p_copy = p.copy()
        self.assertIsNot(p, p_copy)
        self.assertEqual(p, p_copy)

    def test_check(self):
        p = Permissions(user="rwx")
        self.assertTrue(p.check("u_r"))
        self.assertTrue(p.check("u_r", "u_w"))
        self.assertTrue(p.check("u_r", "u_w", "u_x"))
        self.assertFalse(p.check("u_r", "g_w"))
        self.assertFalse(p.check("g_r", "g_w"))
        self.assertFalse(p.check("foo"))

    def test_mode_set(self):
        p = Permissions(user="r")
        self.assertEqual(text_type(p), "r--------")
        p.mode = 0o700
        self.assertEqual(text_type(p), "rwx------")
