# coding: utf-8
import os
import shutil
import tempfile
import sys
import unittest
import pytest

from fs.path import relpath, dirname

from click.testing import CliRunner
from fs.commands import fs2
from fs import errors

try:
    from unittest import mock
except ImportError:
    import mock


class TestFS2(unittest.TestCase):
    """Test OSFS implementation."""

    def _realpath(self, path):
        _path = os.path.join(self.dir_fs2, relpath(path))
        return _path

    def setUp(self):
        self.dir_fs2 = tempfile.mkdtemp("testfs2")
        os.makedirs(self._realpath('a/b/c'), exist_ok=True)
        os.makedirs(self._realpath('a/1'), exist_ok=True)
        for fn in ['a/b/c/d.txt', 'a/b.txt', 'a/0.ini', 'a/1/a1.txt', 'a/1/a2.txt']:
            with open(self._realpath(fn), 'w') as f:
                f.write('\n'.join(str(i) for i in range(100, 110)))
        self.runner = CliRunner()

    def tearDown(self):
        try:
            shutil.rmtree(self.dir_fs2)
        except OSError:
            print(self.dir_fs2, 'Already deleted')

    def test_help(self):
        result = self.runner.invoke(fs2, [])
        print(result.output)
        self.assertEqual(result.exit_code, 0)
        self.assertIn('Usage:', result.output)
        self.assertIn('--help', result.output)

    def test_listopener(self):
        result = self.runner.invoke(fs2, ['--listopener'])
        print(result.output)
        self.assertEqual(result.exit_code, 0)
        self.assertIn('OSFSOpener', result.output)
        self.assertIn('ZipOpener',  result.output)

    def test_ls(self):
        args = ['-u', self._realpath('/'), 'ls', '.', 'a/0.ini', 'a/1', 'no_exists_dir/1.ini', 'a/b/c']
        result = self.runner.invoke(fs2, args, input='N\n')
        print(result.output)
        self.assertNotEqual(result.exit_code, 0)
        self.assertIn('a1.txt',  result.output)

    def test_cat(self):
        args = ['-u', self._realpath('/'), 'cat', 'a/0.ini', 'a/b.txt', 'a', 'no_exists_dir/1.ini']
        result = self.runner.invoke(fs2, args, input='Y\nN\n')
        print(result.output)
        self.assertNotEqual(result.exit_code, 0)

    def test_tree(self):
        args = ['-u', self._realpath('/'), 'tree', 'a/']
        result = self.runner.invoke(fs2, args)
        print(result.output)
        self.assertEqual(result.exit_code, 0)
        self.assertIn('a1.txt',  result.output)

    def test_mkdir(self):
        args = ['-u', self._realpath('/'), 'mkdir', '-p', '1/2/3']
        result = self.runner.invoke(fs2, args)
        self.assertEqual(result.exit_code, 0)
        args = ['-u', self._realpath('/'), 'mkdir', '1/2/3', 'no_exists_dir/abc']
        result = self.runner.invoke(fs2, args, input='N\n')
        print(result.output)
        self.assertNotEqual(result.exit_code, 0)

    def test_cp(self):
        args = ['-u', self._realpath('/'), 'cp', 'a/0.ini', 'a/cp.ini']
        result = self.runner.invoke(fs2, args)
        self.assertEqual(result.exit_code, 0)

    def test_mv(self):
        args = ['-u', self._realpath('/'), 'mv', 'a/cp.ini', 'a/mv.ini']
        result = self.runner.invoke(fs2, args)
        self.assertEqual(result.exit_code, 0)

    def test_rm(self):
        args = ['-u', self._realpath('/'), 'rm', 'a/mv.ini']
        result = self.runner.invoke(fs2, args)
        self.assertEqual(result.exit_code, 0)

    def test_dl(self):
        with self.runner.isolated_filesystem():
            args = ['-u', self._realpath('/'), 'dl', 'a/b', 'a/1', '.']
            result = self.runner.invoke(fs2, args)
            self.assertEqual(result.exit_code, 0)
            # print(__file__, os.getcwd(), os.listdir())
            with open('b/new.txt', 'w') as f:
                f.write('11bb11\n' * 1000)
            args = ['-u', self._realpath('/'), 'up', './', './']
            result = self.runner.invoke(fs2, args)
            self.assertEqual(result.exit_code, 0)

