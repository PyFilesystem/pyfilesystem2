from __future__ import unicode_literals

import errno
import os
import sys
from operator import attrgetter

from six import text_type

from ..path import join
from ..errors import FSError, ResourceNotFound
from .context import ModulePatch


def _not_found(path):
    """Raise an OSError ENOENT error."""
    _error = os.strerror(errno.ENOENT)
    raise OSError(errno.ENOENT, _error, path)


class OsPathExists(ModulePatch):
    module = os.path
    attrib = 'exists'

    def exists(self, context, path):
        _path = context.get_path(path)
        return context.filesystem.exists(_path)


class OsPathLExists(ModulePatch):
    module = os.path
    attrib = 'lexists'

    def lexists(self, context, path):
        _path = context.get_path(path)
        return context.filesystem.exists(_path)


class _OsPathTime(ModulePatch):
    module = os.path
    attrib = 'gettime'
    patch_method = 'gettime'
    time_field = ''

    def gettime(self, context, path):
        _path = context.get_path(path)
        try:
            info = context.filesystem.getdetails(_path)
        except ResourceNotFound:
            _not_found(_path)
        try:
            _time = info.raw['details'][self.time_field]
        except KeyError:
            raise OSError('unable to get time')
        return _time


class OsPathGetatime(_OsPathTime):
    attrib = 'getatime'
    time_field = 'accessed'


class OsPathGetmtime(_OsPathTime):
    attrib = 'getmtime'
    time_field = 'modified'


class OsPathGetctime(_OsPathTime):
    attrib = 'getctime'

    time_field = (
        'metadata_changed'
        if sys.platform == 'linux' else
        'created'
    )


class OsPathGetsize(ModulePatch):
    module = os.path
    attrib = 'getsize'

    def getsize(self, context, path):
        _path = context.get_path(path)
        try:
            return context.filesystem.getsize(_path)
        except ResourceNotFound:
            _not_found(_path)


class OsPathIsfile(ModulePatch):
    module = os.path
    attrib = 'isfile'

    def isfile(self, context, path):
        _path = context.get_path(path)
        try:
            return context.filesystem.isfile(_path)
        except ResourceNotFound:
            _not_found(_path)


class OsPathIsdir(ModulePatch):
    module = os.path
    attrib = 'isdir'

    def isdir(self, context, path):
        _path = context.get_path(path)
        try:
            return context.filesystem.isdir(_path)
        except ResourceNotFound:
            _not_found(_path)


class OsPathIslink(ModulePatch):
    module = os.path
    attrib = 'islink'

    def islink(self, context, path):
        _path = context.get_path(path)
        try:
            return context.filesystem.islink(_path)
        except ResourceNotFound:
            _not_found(_path)


class OsListdir(ModulePatch):
    module = os
    attrib = 'listdir'

    def listdir(self, context, path='.'):
        if not path:
            _not_found(path)
        _path = context.get_path(path)
        try:
            dirlist = context.filesystem.listdir(_path)
        except ResourceNotFound as error:
            _not_found(path)
        except FSError as error:
            raise OSError(text_type(error))
        return dirlist


class OsWalk(ModulePatch):
    module = os
    attrib = 'walk'

    def walk(self, context,
             top, topdown=True, onerror=None, followlinks=False):
        _path = context.get_path(top)
        walk_method = 'depth' if topdown else 'breadth'
        getname = attrgetter('name')
        with context.filesystem.opendir(_path) as dir_fs:
            for _dirpath, _dirs, _files in dir_fs.walk(method=walk_method):
                dirpath = join(_path, _dirpath)
                dirs = [getname(info) for info in _dirs]
                files = [getname(info) for info in _files]
                yield dirpath, dirs, files

