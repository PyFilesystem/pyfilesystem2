# coding: utf-8
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import socket
import os
import platform
import shutil
import tempfile
import time
import unittest
import uuid

import pytest
from six import text_type

from ftplib import error_perm
from ftplib import error_temp

from pyftpdlib.authorizers import DummyAuthorizer

from fs import errors
from fs.opener import open_fs
from fs.ftpfs import FTPFS, ftp_errors
from fs.path import join
from fs.subfs import SubFS
from fs.test import FSTestCases


# Prevent socket timeouts from slowing tests too much
socket.setdefaulttimeout(1)


class TestFTPFSClass(unittest.TestCase):
    def test_parse_ftp_time(self):
        self.assertIsNone(FTPFS._parse_ftp_time("notreallyatime"))
        t = FTPFS._parse_ftp_time("19740705000000")
        self.assertEqual(t, 142214400)

    def test_parse_mlsx(self):
        info = list(
            FTPFS._parse_mlsx(["create=19740705000000;modify=19740705000000; /foo"])
        )[0]
        self.assertEqual(info["details"]["modified"], 142214400)
        self.assertEqual(info["details"]["created"], 142214400)

        info = list(FTPFS._parse_mlsx(["foo=bar; .."]))
        self.assertEqual(info, [])

    def test_parse_mlsx_type(self):
        lines = [
            "Type=cdir;Modify=20180731114724;UNIX.mode=0755; /tmp",
            "Type=pdir;Modify=20180731112024;UNIX.mode=0775; /",
            "Type=file;Size=331523;Modify=20180731112041;UNIX.mode=0644; a.csv",
            "Type=file;Size=368340;Modify=20180731112041;UNIX.mode=0644; b.csv",
        ]
        expected = [
            {
                "basic": {"name": "a.csv", "is_dir": False},
                "ftp": {
                    "type": "file",
                    "size": "331523",
                    "modify": "20180731112041",
                    "unix.mode": "0644",
                },
                "details": {"type": 2, "size": 331523, "modified": 1533036041},
            },
            {
                "basic": {"name": "b.csv", "is_dir": False},
                "ftp": {
                    "type": "file",
                    "size": "368340",
                    "modify": "20180731112041",
                    "unix.mode": "0644",
                },
                "details": {"type": 2, "size": 368340, "modified": 1533036041},
            },
        ]
        info = list(FTPFS._parse_mlsx(lines))
        self.assertEqual(info, expected)

    def test_opener(self):
        ftp_fs = open_fs("ftp://will:wfc@ftp.example.org")
        self.assertIsInstance(ftp_fs, FTPFS)
        self.assertEqual(ftp_fs.host, "ftp.example.org")


class TestFTPErrors(unittest.TestCase):
    """Test the ftp_errors context manager."""

    def test_manager(self):
        mem_fs = open_fs("mem://")

        with self.assertRaises(errors.ResourceError):
            with ftp_errors(mem_fs, path="foo"):
                raise error_temp

        with self.assertRaises(errors.OperationFailed):
            with ftp_errors(mem_fs):
                raise error_temp

        with self.assertRaises(errors.InsufficientStorage):
            with ftp_errors(mem_fs):
                raise error_perm("552 foo")

        with self.assertRaises(errors.ResourceNotFound):
            with ftp_errors(mem_fs):
                raise error_perm("501 foo")

        with self.assertRaises(errors.PermissionDenied):
            with ftp_errors(mem_fs):
                raise error_perm("999 foo")

    def test_manager_with_host(self):
        mem_fs = open_fs("mem://")
        mem_fs.host = "ftp.example.com"

        with self.assertRaises(errors.RemoteConnectionError) as err_info:
            with ftp_errors(mem_fs):
                raise EOFError
        self.assertEqual(str(err_info.exception), "lost connection to ftp.example.com")

        with self.assertRaises(errors.RemoteConnectionError) as err_info:
            with ftp_errors(mem_fs):
                raise socket.error
        self.assertEqual(
            str(err_info.exception), "unable to connect to ftp.example.com"
        )


@pytest.mark.slow
class TestFTPFS(FSTestCases, unittest.TestCase):

    user = "user"
    pasw = "1234"

    @classmethod
    def setUpClass(cls):
        from pyftpdlib.test import ThreadedTestFTPd

        super(TestFTPFS, cls).setUpClass()

        cls._temp_dir = tempfile.mkdtemp("ftpfs2tests")
        cls._temp_path = os.path.join(cls._temp_dir, text_type(uuid.uuid4()))
        os.mkdir(cls._temp_path)

        cls.server = ThreadedTestFTPd()
        cls.server.shutdown_after = -1
        cls.server.handler.authorizer = DummyAuthorizer()
        cls.server.handler.authorizer.add_user(
            cls.user, cls.pasw, cls._temp_path, perm="elradfmw"
        )
        cls.server.handler.authorizer.add_anonymous(cls._temp_path)
        cls.server.start()

        # Don't know why this is necessary on Windows
        if platform.system() == "Windows":
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
        return open_fs(
            "ftp://{}:{}@{}:{}".format(
                self.user, self.pasw, self.server.host, self.server.port
            )
        )

    def tearDown(self):
        shutil.rmtree(self._temp_path)
        os.mkdir(self._temp_path)
        super(TestFTPFS, self).tearDown()

    def test_ftp_url(self):
        self.assertEqual(
            self.fs.ftp_url,
            "ftp://{}:{}@{}:{}".format(
                self.user, self.pasw, self.server.host, self.server.port
            ),
        )

    def test_geturl(self):
        self.fs.makedir("foo")
        self.fs.create("bar")
        self.fs.create("foo/bar")
        self.assertEqual(
            self.fs.geturl("foo"),
            "ftp://{}:{}@{}:{}/foo".format(
                self.user, self.pasw, self.server.host, self.server.port
            ),
        )
        self.assertEqual(
            self.fs.geturl("bar"),
            "ftp://{}:{}@{}:{}/bar".format(
                self.user, self.pasw, self.server.host, self.server.port
            ),
        )
        self.assertEqual(
            self.fs.geturl("foo/bar"),
            "ftp://{}:{}@{}:{}/foo/bar".format(
                self.user, self.pasw, self.server.host, self.server.port
            ),
        )

    def test_host(self):
        self.assertEqual(self.fs.host, self.server.host)

    def test_connection_error(self):
        fs = FTPFS("ftp.not.a.chance", timeout=1)
        with self.assertRaises(errors.RemoteConnectionError):
            fs.listdir("/")

        with self.assertRaises(errors.RemoteConnectionError):
            fs.makedir("foo")

        with self.assertRaises(errors.RemoteConnectionError):
            fs.open("foo.txt")

    def test_getmeta_unicode_path(self):
        self.assertTrue(self.fs.getmeta().get("unicode_paths"))
        self.fs.features
        del self.fs.features["UTF8"]
        self.assertFalse(self.fs.getmeta().get("unicode_paths"))

    def test_opener_path(self):
        self.fs.makedir("foo")
        self.fs.writetext("foo/bar", "baz")
        ftp_fs = open_fs(
            "ftp://user:1234@{}:{}/foo".format(self.server.host, self.server.port)
        )
        self.assertIsInstance(ftp_fs, SubFS)
        self.assertEqual(ftp_fs.readtext("bar"), "baz")
        ftp_fs.close()

    def test_create(self):

        directory = join("home", self.user, "test", "directory")
        base = "ftp://user:1234@{}:{}/foo".format(self.server.host, self.server.port)
        url = "{}/{}".format(base, directory)

        # Make sure unexisting directory raises `CreateFailed`
        with self.assertRaises(errors.CreateFailed):
            ftp_fs = open_fs(url)

        # Open with `create` and try touching a file
        with open_fs(url, create=True) as ftp_fs:
            ftp_fs.touch("foo")

        # Open the base filesystem and check the subdirectory exists
        with open_fs(base) as ftp_fs:
            self.assertTrue(ftp_fs.isdir(directory))
            self.assertTrue(ftp_fs.isfile(join(directory, "foo")))

        # Open without `create` and check the file exists
        with open_fs(url) as ftp_fs:
            self.assertTrue(ftp_fs.isfile("foo"))

        # Open with create and check this does fail
        with open_fs(url, create=True) as ftp_fs:
            self.assertTrue(ftp_fs.isfile("foo"))


class TestFTPFSNoMLSD(TestFTPFS):
    def make_fs(self):
        ftp_fs = super(TestFTPFSNoMLSD, self).make_fs()
        ftp_fs.features
        del ftp_fs.features["MLST"]
        return ftp_fs

    def test_features(self):
        pass


@pytest.mark.slow
class TestAnonFTPFS(FSTestCases, unittest.TestCase):

    user = "anonymous"
    pasw = ""

    @classmethod
    def setUpClass(cls):
        from pyftpdlib.test import ThreadedTestFTPd

        super(TestAnonFTPFS, cls).setUpClass()

        cls._temp_dir = tempfile.mkdtemp("ftpfs2tests")
        cls._temp_path = os.path.join(cls._temp_dir, text_type(uuid.uuid4()))
        os.mkdir(cls._temp_path)

        cls.server = ThreadedTestFTPd()
        cls.server.shutdown_after = -1
        cls.server.handler.authorizer = DummyAuthorizer()
        cls.server.handler.authorizer.add_anonymous(cls._temp_path, perm="elradfmw")
        cls.server.start()

        # Don't know why this is necessary on Windows
        if platform.system() == "Windows":
            time.sleep(0.1)
        # Poll until a connection can be made
        if not cls.server.is_alive():
            raise RuntimeError("could not start FTP server.")

    @classmethod
    def tearDownClass(cls):
        cls.server.stop()
        shutil.rmtree(cls._temp_dir)
        super(TestAnonFTPFS, cls).tearDownClass()

    def make_fs(self):
        return open_fs("ftp://{}:{}".format(self.server.host, self.server.port))

    def tearDown(self):
        shutil.rmtree(self._temp_path)
        os.mkdir(self._temp_path)
        super(TestAnonFTPFS, self).tearDown()

    def test_ftp_url(self):
        self.assertEqual(
            self.fs.ftp_url, "ftp://{}:{}".format(self.server.host, self.server.port)
        )

    def test_geturl(self):
        self.fs.makedir("foo")
        self.fs.create("bar")
        self.fs.create("foo/bar")
        self.assertEqual(
            self.fs.geturl("foo"),
            "ftp://{}:{}/foo".format(self.server.host, self.server.port),
        )
        self.assertEqual(
            self.fs.geturl("bar"),
            "ftp://{}:{}/bar".format(self.server.host, self.server.port),
        )
        self.assertEqual(
            self.fs.geturl("foo/bar"),
            "ftp://{}:{}/foo/bar".format(self.server.host, self.server.port),
        )
