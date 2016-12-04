from __future__ import unicode_literals

import unittest

from fs import errors
from fs import open_fs
from fs import wrap


class TestWrap(unittest.TestCase):

    def test_readonly(self):
        mem_fs = open_fs('mem://')
        fs = wrap.read_only(mem_fs)

        with self.assertRaises(errors.ResourceReadOnly):
            fs.open('foo', 'w')

        with self.assertRaises(errors.ResourceReadOnly):
            fs.appendtext('foo', 'bar')

        with self.assertRaises(errors.ResourceReadOnly):
            fs.appendbytes('foo', b'bar')

        with self.assertRaises(errors.ResourceReadOnly):
            fs.makedir('foo')

        with self.assertRaises(errors.ResourceReadOnly):
            fs.move('foo', 'bar')

        with self.assertRaises(errors.ResourceReadOnly):
            fs.openbin('foo', 'w')

        with self.assertRaises(errors.ResourceReadOnly):
            fs.remove('foo')

        with self.assertRaises(errors.ResourceReadOnly):
            fs.removedir('foo')

        with self.assertRaises(errors.ResourceReadOnly):
            fs.setinfo('foo', {})

        with self.assertRaises(errors.ResourceReadOnly):
            fs.settimes('foo', {})

        with self.assertRaises(errors.ResourceReadOnly):
            fs.copy('foo', 'bar')

        with self.assertRaises(errors.ResourceReadOnly):
            fs.create('foo')

        with self.assertRaises(errors.ResourceReadOnly):
            fs.settext('foo', 'bar')

        with self.assertRaises(errors.ResourceReadOnly):
            fs.setbytes('foo', b'bar')

        with self.assertRaises(errors.ResourceReadOnly):
            fs.makedirs('foo/bar')

        with self.assertRaises(errors.ResourceReadOnly):
            fs.touch('foo')

        with self.assertRaises(errors.ResourceReadOnly):
            fs.setbinfile('foo', None)

        with self.assertRaises(errors.ResourceReadOnly):
            fs.setfile('foo', None)

        self.assertTrue(mem_fs.isempty('/'))
        mem_fs.setbytes('file', b'read me')
        with fs.openbin('file') as read_file:
            self.assertEqual(read_file.read(), b'read me')

        with fs.open('file', 'rb') as read_file:
            self.assertEqual(read_file.read(), b'read me')

    def test_cachedir(self):
        mem_fs = open_fs('mem://')
        mem_fs.makedirs('foo/bar/baz')
        mem_fs.touch('egg')

        fs = wrap.cache_directory(mem_fs)
        self.assertEqual(
            sorted(fs.listdir('/')),
            ['egg', 'foo']
        )
        self.assertEqual(
            sorted(fs.listdir('/')),
            ['egg', 'foo']
        )
        self.assertTrue(fs.isdir('foo'))
        self.assertTrue(fs.isdir('foo'))
        self.assertTrue(fs.isfile('egg'))
        self.assertTrue(fs.isfile('egg'))

        self.assertEqual(fs.getinfo('foo'), mem_fs.getinfo('foo'))
        self.assertEqual(fs.getinfo('foo'), mem_fs.getinfo('foo'))

        self.assertEqual(fs.getinfo('/'), mem_fs.getinfo('/'))
        self.assertEqual(fs.getinfo('/'), mem_fs.getinfo('/'))

        with self.assertRaises(errors.ResourceNotFound):
            fs.getinfo('/foofoo')

