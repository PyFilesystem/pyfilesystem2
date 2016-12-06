from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import ftplib
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
import uuid

from six import text_type
from six.moves.urllib.request import urlopen

from ftplib import error_perm
from ftplib import error_temp

from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import FTPServer

from fs import errors
from fs.opener import open_fs
from fs.ftpfs import ftp_errors

from nose.plugins.attrib import attr


_WINDOWS_PLATFORM = platform.system() == 'Windows'


if __name__ == "__main__":
    # Run an ftp server that exposes a given directory
    import sys
    authorizer = DummyAuthorizer()
    authorizer.add_user("user", "12345", sys.argv[1], perm="elradfmw")
    authorizer.add_anonymous(sys.argv[1])

    handler = FTPHandler
    handler.authorizer = authorizer
    address = ("127.0.0.1", int(sys.argv[2]))

    ftpd = FTPServer(address, handler)

    sys.stdout.write('serving\n')
    sys.stdout.flush()
    ftpd.serve_forever()
    sys.exit(0)


from fs.test import FSTestCases

ftp_port_offset = 0
ftp_port = 30000 + (os.getpid() % 8)


class TestFTPFSClass(unittest.TestCase):

    def test_parse_ftp_time(self):
        from fs.ftpfs import FTPFS
        self.assertIsNone(FTPFS._parse_ftp_time('notreallyatime'))
        t = FTPFS._parse_ftp_time('19740705000000')
        self.assertEqual(t, 142214400)

    def test_parse_mlsx(self):
        from fs.ftpfs import FTPFS
        info = list(
            FTPFS._parse_mlsx(['create=19740705000000;modify=19740705000000; /foo'])
        )[0]
        self.assertEqual(info['details']['modified'], 142214400)
        self.assertEqual(info['details']['created'], 142214400)

        info = list(FTPFS._parse_mlsx(['foo=bar; ..']))
        self.assertEqual(info, [])

    def test_opener(self):
        from fs.ftpfs import FTPFS
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



@attr('slow')
class TestFTPFS(FSTestCases, unittest.TestCase):

    def make_fs(self):
        from fs.ftpfs import FTPFS
        global ftp_port_offset
        temp_path = os.path.join(self._temp_dir, text_type(uuid.uuid4()))
        _ftp_port = ftp_port + ftp_port_offset
        ftp_port_offset += 1

        os.mkdir(temp_path)
        env = os.environ.copy()

        server = subprocess.Popen(
            [
                sys.executable,
                os.path.abspath(__file__),
                temp_path,
                text_type(_ftp_port)
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env
        )
        server.stdout.readline()

        if _WINDOWS_PLATFORM:
            # Don't know why this is necessary on Windows
            time.sleep(0.1)

        # Poll until a connection can be made
        start_time = time.time()
        while time.time() - start_time < 5:
            try:
                ftpurl = urlopen('ftp://127.0.0.1:{}'.format(_ftp_port))
            except IOError:
                time.sleep(0)
            else:
                ftpurl.read()
                ftpurl.close()
                break
        else:
            raise Exception("unable to start ftp server")
        self.servers.append(server)

        fs = FTPFS(
            '127.0.0.1',
            user='user',
            passwd='12345',
            port=_ftp_port,
            timeout=5.0
        )
        return fs

    def setUp(self):
        self.servers = []
        self._temp_dir = tempfile.mkdtemp('ftpfs2tests')
        super(TestFTPFS, self).setUp()

    def tearDown(self):
        while self.servers:
            server = self.servers.pop(0)
            if sys.platform == 'win32':
                os.popen('TASKKILL /PID {} /F'.format(server.pid))
            else:
                os.system('kill {}'.format(server.pid))
        shutil.rmtree(self._temp_dir)
        super(TestFTPFS, self).tearDown()

    def test_connection_error(self):
        from fs.ftpfs import FTPFS
        fs = FTPFS('ftp.not.a.chance', timeout=1)
        with self.assertRaises(errors.RemoteConnectionError):
            fs.listdir('/')

        with self.assertRaises(errors.RemoteConnectionError):
            fs.makedir('foo')

        with self.assertRaises(errors.RemoteConnectionError):
            fs.open('foo.txt')

    def test_features(self):
        def broken_sendcmd(cmd):
            raise ftplib.error_perm('nope')
        self.fs.ftp.sendcmd = broken_sendcmd
        self.assertEqual(self.fs.features, {})


class TestFTPFSNoMLSD(TestFTPFS):

    def make_fs(self):
        ftp_fs = super(TestFTPFSNoMLSD, self).make_fs()
        ftp_fs.features
        del ftp_fs.features['MLST']
        return ftp_fs

    def test_features(self):
        pass
