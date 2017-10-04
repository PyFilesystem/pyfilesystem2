# coding: utf-8
"""`OSFS` opener definition.
"""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

from .base import Opener

class OSFSOpener(Opener):
    """`OSFS` opener.
    """

    protocols = ['file', 'osfs']

    def open_fs(self, fs_url, parse_result, writeable, create, cwd):
        from ..osfs import OSFS
        from os.path import abspath, expanduser, normpath, join
        _path = abspath(join(cwd, expanduser(parse_result.resource)))
        path = normpath(_path)
        osfs = OSFS(path, create=create)
        return osfs
