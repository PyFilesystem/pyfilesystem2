# coding: utf-8
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import socket
import ftplib
import os
import platform
import shutil
import tempfile
import time
import unittest
import uuid

from six import text_type

from ftplib import error_perm
from ftplib import error_temp

from pyftpdlib.authorizers import DummyAuthorizer

from fs import errors
from fs.opener import open_fs
from fs.ftpfs import FTPFS, ftp_errors
from fs.test import FSTestCases


# Prevent socket timeouts from slowing tests too much
socket.setdefaulttimeout(1)


class TestFTPFSClass(unittest.TestCase):

    def test_parse_ftp_time(self):
        self.assertIsNone(FTPFS._parse_ftp_time('notreallyatime'))
        t = FTPFS._parse_ftp_time('19740705000000')
        self.assertEqual(t, 142214400)

    def test_parse_mlsx(self):
        info = list(
            FTPFS._parse_mlsx(['create=19740705000000;modify=19740705000000; /foo'])
        )[0]
        self.assertEqual(info['details']['modified'], 142214400)
        self.assertEqual(info['details']['created'], 142214400)

        info = list(FTPFS._parse_mlsx(['foo=bar; ..']))
        self.assertEqual(info, [])

    def test_opener(self):
        ftp_fs = open_fs('ftp://will:wfc@ftp.example.org')
        self.assertIsInstance(ftp_fs, FTPFS)
        self.assertEqual(ftp_fs.host, 'ftp.example.org')


class TestFTPErrors(unittest.TestCase):
    """Test the ftp_errors context manager."""

    def test_manager(self):
        mem_fs = open_fs('mem://')

        with self.assertRaises(errors.ResourceError):
            with ftp_errors(mem_fs, path='foo'):
                raise error_temp

        with self.assertRaises(errors.OperationFailed):
            with ftp_errors(mem_fs):
                raise error_temp

        with self.assertRaises(errors.InsufficientStorage):
            with ftp_errors(mem_fs):
                raise error_perm('552 foo')

        with self.assertRaises(errors.ResourceNotFound):
            with ftp_errors(mem_fs):
                raise error_perm('501 foo')

        with self.assertRaises(errors.PermissionDenied):
            with ftp_errors(mem_fs):
                raise error_perm('999 foo')


class TestFTPFS(FSTestCases, unittest.TestCase):

    user = 'user'
    pasw = '1234'

    @classmethod
    def setUpClass(cls):
        from pyftpdlib.test import ThreadedTestFTPd
        super(TestFTPFS, cls).setUpClass()

        cls._temp_dir = tempfile.mkdtemp('ftpfs2tests')
        cls._temp_path = os.path.join(cls._temp_dir, text_type(uuid.uuid4()))
        os.mkdir(cls._temp_path)

        cls.server = ThreadedTestFTPd()
        cls.server.shutdown_after = -1
        cls.server.handler.authorizer = DummyAuthorizer()
        cls.server.handler.authorizer.add_user(
            cls.user, cls.pasw, cls._temp_path, perm="elradfmw")
        cls.server.handler.authorizer.add_anonymous(cls._temp_path)
        cls.server.start()

        # Don't know why this is necessary on Windows
        if platform.system() == 'Windows':
            time.sleep(0.1)
        # Poll until a connection can be made
        if not cls.server.is_alive():
            raise RuntimeError("could not start FTP server.")

    @classmethod
    def tearDownClass(cls):
        cls.server.stop()
        shutil.rmtree(cls._temp_dir)
        super(TestFTPFS, cls).tearDownClass()

    def make_fs(self):
        return open_fs('ftp://{}:{}@{}:{}'.format(
            self.user, self.pasw, self.server.host, self.server.port
        ))

    def tearDown(self):
        shutil.rmtree(self._temp_path)
        os.mkdir(self._temp_path)
        super(TestFTPFS, self).tearDown()

    def test_ftp_url(self):
        self.assertTrue(self.fs.ftp_url.startswith('ftp://127.0.0.1'))

    def test_host(self):
        self.assertEqual(self.fs.host, self.server.host)

    #@attr('slow')
    def test_connection_error(self):
        fs = FTPFS('ftp.not.a.chance', timeout=1)
        with self.assertRaises(errors.RemoteConnectionError):
            fs.listdir('/')

        with self.assertRaises(errors.RemoteConnectionError):
            fs.makedir('foo')

        with self.assertRaises(errors.RemoteConnectionError):
            fs.open('foo.txt')

    def test_getmeta_unicode_path(self):
        self.assertTrue(self.fs.getmeta().get('unicode_paths'))
        self.fs.features
        del self.fs.features['UTF8']
        self.assertFalse(self.fs.getmeta().get('unicode_paths'))


class TestFTPFSNoMLSD(TestFTPFS):

    def make_fs(self):
        ftp_fs = super(TestFTPFSNoMLSD, self).make_fs()
        ftp_fs.features
        del ftp_fs.features['MLST']
        return ftp_fs

    def test_features(self):
        pass
