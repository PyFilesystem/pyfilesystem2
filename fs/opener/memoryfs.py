# coding: utf-8
"""Defines the MemOpener."""

from ._base import Opener
from ._registry import registry

@registry.install
class MemOpener(Opener):
    protocols = ['mem']

    def open_fs(self, fs_url, parse_result, writeable, create, cwd):
        from ..memoryfs import MemoryFS
        mem_fs = MemoryFS()
        return mem_fs
