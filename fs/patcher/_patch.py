from __future__ import unicode_literals

from six import PY3

from .context import PatchContext
from . import common_patches
from ..opener import open_fs
from ..base import FS


PATCHES = [
    common_patches.OsPathExists(),
    common_patches.OsPathLExists(),
    common_patches.OsPathGetatime(),
    common_patches.OsPathGetmtime(),
    common_patches.OsPathGetctime(),
    common_patches.OsPathGetsize(),
    common_patches.OsPathIsfile(),
    common_patches.OsPathIsdir(),
    common_patches.OsPathIslink(),
    common_patches.OsListdir(),
]

if PY3:
    from . import py3_patches



def patch(fs_url, patches=None, cwd='/'):
    """
    Patch a filesystem over Python builtins.

    """

    if isinstance(fs_url, FS):
        filesystem = fs_url
        auto_close = True
    else:
        filesystem = open_fs(fs_url)
        auto_close = False

    _patches = (
        patches
        if patches is not None
        else PATCHES
    )

    return PatchContext(
        filesystem,
        PATCHES,
        cwd=cwd,
        auto_close=auto_close
    )
