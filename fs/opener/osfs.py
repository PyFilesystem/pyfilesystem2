# coding: utf-8
"""Defines the OSFSOpener."""

from .base import Opener

class OSFSOpener(Opener):
    protocols = ['file', 'osfs']

    def open_fs(self, fs_url, parse_result, writeable, create, cwd):
        from ..osfs import OSFS
        from os.path import abspath, normpath, join
        _path = abspath(join(cwd, parse_result.resource))
        path = normpath(_path)
        osfs = OSFS(path, create=create)
        return osfs
