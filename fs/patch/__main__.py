from __future__ import unicode_literals

import logging

logging.basicConfig(level=logging.DEBUG)

from . import patch


from fs import open_fs

fs = open_fs('mem://')
fs.touch('foo')
fs.makedir('bar').settext('egg', 'Hello, World!')

import os

with patch(fs):
    print(os.listdir('/'))
    print(os.getcwd())
    os.chdir('bar')
    print(os.listdir('.'))
    print(open('egg').read())

