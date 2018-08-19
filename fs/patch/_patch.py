from __future__ import unicode_literals

from .. import open_fs
from .base import PatchContext


def patch(fs_url, auto_close=True):
    if isinstance(fs_url, str):
        fs_obj = open_fs(fs_url)
        return PatchContext(fs_obj, auto_close=True)
    else:
        return PatchContext(fs_url, auto_close=auto_close)
