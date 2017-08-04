# coding: utf-8
"""Defines the ZipOpener."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

from .base import Opener

class ZipOpener(Opener):
    protocols = ['zip']

    def open_fs(self, fs_url, parse_result, writeable, create, cwd):
        from ..zipfs import ZipFS
        zip_fs = ZipFS(
            parse_result.resource,
            write=create
        )
        return zip_fs
