from __future__ import unicode_literals

import errno
import os
import sys
from operator import attrgetter

from six import text_type

from ..path import join
from ..errors import FSError, ResourceNotFound
from .context import ModulePatch




class OsWalk(ModulePatch):
    module = os
    attrib = 'walk'

    def walk(self, context,
             top, topdown=True, onerror=None, followlines=False):
        _path = context.get_path(top)

        walk_method = (
            'depth'
            if topdown else
            'breadth'
        )
        getname = attrgetter('name')
        with context.filesystem.opendir(_path) as dir_fs:
            for _dirpath, _dirs, _files in dir_fs.walk(method=walk_method):
                dirpath = join(_path, _dirpath)
                dirs = [getname(info) for info in _dirs]
                files = [getname(info) for info in _files]
                yield dirpath, dirs, files
