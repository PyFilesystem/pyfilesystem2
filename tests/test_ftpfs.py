from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

from six import text_type

from six.moves.urllib.request import urlopen

import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
import uuid


from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import FTPServer

from fs import errors
from fs.ftpfs import FTPFS


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


from .test_fs import FSTestCases

ftp_port = 30000


class TestFTPFS(FSTestCases, unittest.TestCase):

    def make_fs(self):
        global ftp_port
        temp_path = os.path.join(self._temp_dir, text_type(uuid.uuid4()))
        _ftp_port = ftp_port
        ftp_port += 1

        os.mkdir(temp_path)
        env = os.environ.copy()
        env['PYTHONPATH'] = os.path.join(
            os.getcwd(),
            env.get('PYTHONPATH', '')
        )
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
        fs = FTPFS('ftp.not.a.chance')
        with self.assertRaises(errors.RemoteConnectionError):
            fs.listdir('/')
