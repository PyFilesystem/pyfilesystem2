from __future__ import unicode_literals

from fs import open_fs
from . import patch

import os
from os import listdir
from os.path import exists
fs = open_fs('mem://')
foo = fs.makedir('foo')
foo.touch('bar1')
foo.touch('bar2')
with patch(fs):
    d = os.listdir('/')
    print(d)
    print(listdir('/'))
    # print('--')
    # print(os.path.exists('foo'))
    # print(exists('foo'))
    # print('--')
    # print(os.path.isfile('foo'))
    # print(os.path.getatime('foo'))

print(os.listdir('/'))
