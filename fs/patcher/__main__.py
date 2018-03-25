from __future__ import unicode_literals

from fs import open_fs
from . import patch

import os
fs = open_fs('mem://')
foo = fs.makedir('foo')
foo.touch('bar1')
foo.touch('bar2')
with patch(fs):
    d = os.listdir('/')
    print(d)
    print os.path.exists('foo')
    print os.path.isfile('foo')
    print os.path.getatime('foo')
print(os.listdir('/'))
