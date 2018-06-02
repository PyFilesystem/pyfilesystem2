from __future__ import unicode_literals

import builtins
import errno
import os
import sys
from operator import attrgetter

from six import text_type

from ..path import join
from ..errors import FSError, ResourceNotFound
from .context import ModulePatch, CodePatch

from . import stack


def _not_found(path):
    """Raise an OSError ENOENT error."""
    _error = os.strerror(errno.ENOENT)
    raise OSError(errno.ENOENT, _error, path)


from fs.patcher.stack import get_context

class OsPathExists(CodePatch):
    module = os.path
    attrib = 'exists'

    def exists(path):
        from fs.patcher.stack import get_context
        context = get_context()
        _path = context.get_path(path)
        return context.filesystem.exists(_path)


class OsPathLExists(CodePatch):
    module = os.path
    attrib = 'lexists'

    def lexists(path):
        from fs.patcher.stack import get_context
        context = get_context()
        _path = context.get_path(path)
        return context.filesystem.exists(_path)


class OsPathGetatime(CodePatch):
    module = os.path
    attrib = 'getatime'

    def getatime(path):
        from fs.patcher.stack import get_context
        context = get_context()
        _path = context.get_path(path)
        try:
            info = context.filesystem.getdetails(_path)
        except ResourceNotFound:
            _not_found(_path)
        try:
            _time = info.raw['details']['accessed']
        except KeyError:
            raise OSError('unable to get time')
        return _time


class OsPathGetmtime(CodePatch):
    module = os.path
    attrib = 'getmtime'

    def getmtime(path):
        from fs.patcher.stack import get_context
        context = get_context()
        _path = context.get_path(path)
        try:
            info = context.filesystem.getdetails(_path)
        except ResourceNotFound:
            _not_found(_path)
        try:
            _time = info.raw['details']['modified']
        except KeyError:
            raise OSError('unable to get time')
        return _time


class OsPathGetctime(CodePatch):
    module = os.path
    attrib = 'getctime'

    def getctime(path):
        from fs.patcher.stack import get_context
        context = get_context()
        _path = context.get_path(path)
        try:
            info = context.filesystem.getdetails(_path)
        except ResourceNotFound:
            _not_found(_path)
        time_field = (
            'metadata_changed'
            if sys.platform == 'linux' else
            'created'
        )
        try:
            _time = info.raw['details'][time_field]
        except KeyError:
            raise OSError('unable to get time')
        return _time


class OsPathGetsize(CodePatch):
    module = os.path
    attrib = 'getsize'

    def getsize(path):
        from fs.patcher.stack import get_context
        context = get_context()
        _path = context.get_path(path)
        try:
            return context.filesystem.getsize(_path)
        except ResourceNotFound:
            _not_found(_path)


class OsPathIsfile(CodePatch):
    module = os.path
    attrib = 'isfile'

    def isfile(path):
        from fs.patcher.stack import get_context
        from fs.errors import ResourceNotFound
        context = get_context()
        _path = context.get_path(path)
        try:
            return context.filesystem.isfile(_path)
        except ResourceNotFound:
            _not_found(_path)


class OsPathIsdir(CodePatch):
    module = os.path
    attrib = 'isdir'

    def isdir(path):
        from fs.patcher.stack import get_context
        context = get_context()
        _path = context.get_path(path)
        try:
            return context.filesystem.isdir(_path)
        except ResourceNotFound:
            _not_found(_path)


class OsPathIslink(CodePatch):
    module = os.path
    attrib = 'islink'

    def islink(path):
        from fs.patcher.stack import get_context
        context = get_context()
        _path = self.context.get_path(path)
        try:
            return self.context.filesystem.islink(_path)
        except ResourceNotFound:
            _not_found(_path)


class OsListdir(ModulePatch):
    module = os
    attrib = 'listdir'

    def listdir(self, path='.'):
        if not path:
            _not_found(path)
        _path = self.context.get_path(path)
        try:
            dirlist = self.context.filesystem.listdir(_path)
        except ResourceNotFound as error:
            _not_found(path)
        except FSError as error:
            raise OSError(text_type(error))
        return dirlist


class OsWalk(ModulePatch):
    module = os
    attrib = 'walk'

    def walk(self, top, topdown=True, onerror=None, followlinks=False):
        _path = self.context.get_path(top)
        walk_method = 'depth' if topdown else 'breadth'
        getname = attrgetter('name')
        with self.context.filesystem.opendir(_path) as dir_fs:
            for _dirpath, _dirs, _files in dir_fs.walk(method=walk_method):
                dirpath = join(_path, _dirpath)
                dirs = [getname(info) for info in _dirs]
                files = [getname(info) for info in _files]
                yield dirpath, dirs, files

