"""Defines the OSFSOpener."""
from ._base import Opener
from ._registry import registry

@registry.install
class OSFSOpener(Opener):
    protocols = ['file', 'osfs']

    def open_fs(self, fs_url, parse_result, writeable, create, cwd):
        from ..osfs import OSFS
        from os.path import abspath, normpath, join
        _path = abspath(join(cwd, parse_result.resource))
        path = normpath(_path)
        osfs = OSFS(path, create=create)
        return osfs
