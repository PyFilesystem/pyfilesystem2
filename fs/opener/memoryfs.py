# coding: utf-8
"""`MemoryFS` opener definition.
"""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

from .base import Opener

class MemOpener(Opener):
    """`MemoryFS` opener.
    """

    protocols = ['mem']

    def open_fs(self, fs_url, parse_result, writeable, create, cwd):
        from ..memoryfs import MemoryFS
        mem_fs = MemoryFS()
        return mem_fs
