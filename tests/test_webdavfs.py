from __future__ import unicode_literals

import json
import os
import unittest

from fs import webdavfs
from fs.test import FSTestCases

from nose.plugins.attrib import attr

webdav_config_file = os.path.join(os.path.dirname(__file__),
                                  'webdav_config.json')


@attr('slow')
class TestWebDAVFS(FSTestCases, unittest.TestCase):
    """Test WebDAVFS implementation."""

    def make_fs(self):
        with open(webdav_config_file) as webdav_config:
            conf = json.load(webdav_config)
        url = conf['url']
        creds = {'login': conf['login'],
                 'password': conf['password']}
        root = conf['root']
        return webdavfs.WebDAVFS(url, creds, root)

    def destroy_fs(self, fs):
        for item in fs.client.list('/'):
            fs.client.clean(item)
        super(TestWebDAVFS, self).destroy_fs(fs)
