# coding: utf-8
"""Defines the TempOpener."""

from .base import Opener

class TempOpener(Opener):
    protocols = ['temp']

    def open_fs(self, fs_url, parse_result, writeable, create, cwd):
        from ..tempfs import TempFS
        temp_fs = TempFS(identifier=parse_result.resource)
        return temp_fs
