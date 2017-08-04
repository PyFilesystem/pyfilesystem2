# coding: utf-8
"""Defines the TarOpener."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

from .base import Opener

class TarOpener(Opener):
    protocols = ['tar']

    def open_fs(self, fs_url, parse_result, writeable, create, cwd):
        from ..tarfs import TarFS
        tar_fs = TarFS(
            parse_result.resource,
            write=create
        )
        return tar_fs
