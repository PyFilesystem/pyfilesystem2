# coding: utf-8
"""Defines the ZipOpener."""

from ._base import Opener
from ._registry import registry

@registry.install
class ZipOpener(Opener):
    protocols = ['zip']

    def open_fs(self, fs_url, parse_result, writeable, create, cwd):
        from ..zipfs import ZipFS
        zip_fs = ZipFS(
            parse_result.resource,
            write=create
        )
        return zip_fs
