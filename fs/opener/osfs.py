# coding: utf-8
"""`OSFS` opener definition.
"""

from __future__ import absolute_import, print_function, unicode_literals

import typing

from .base import Opener
from .registry import registry

if typing.TYPE_CHECKING:
    from typing import Text

    from ..osfs import OSFS  # noqa: F401
    from .parse import ParseResult


@registry.install
class OSFSOpener(Opener):
    """`OSFS` opener."""

    protocols = ["file", "osfs"]

    def open_fs(
        self,
        fs_url,  # type: Text
        parse_result,  # type: ParseResult
        writeable,  # type: bool
        create,  # type: bool
        cwd,  # type: Text
    ):
        # type: (...) -> OSFS
        from os.path import abspath, expanduser, join, normpath

        from ..osfs import OSFS

        _path = abspath(join(cwd, expanduser(parse_result.resource)))
        path = normpath(_path)
        osfs = OSFS(path, create=create)
        return osfs
