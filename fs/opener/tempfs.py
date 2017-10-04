# coding: utf-8
"""`TempFS` opener definition.
"""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

from .base import Opener

class TempOpener(Opener):
    """`TempFS` opener.
    """
    
    protocols = ['temp']

    def open_fs(self, fs_url, parse_result, writeable, create, cwd):
        from ..tempfs import TempFS
        temp_fs = TempFS(identifier=parse_result.resource)
        return temp_fs
