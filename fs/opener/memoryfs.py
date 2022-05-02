# coding: utf-8
"""`MemoryFS` opener definition.
"""

from __future__ import absolute_import, print_function, unicode_literals

import typing

from .base import Opener
from .registry import registry

if typing.TYPE_CHECKING:
    from typing import Text

    from ..memoryfs import MemoryFS  # noqa: F401
    from .parse import ParseResult


@registry.install
class MemOpener(Opener):
    """`MemoryFS` opener."""

    protocols = ["mem"]

    def open_fs(
        self,
        fs_url,  # type: Text
        parse_result,  # type: ParseResult
        writeable,  # type: bool
        create,  # type: bool
        cwd,  # type: Text
    ):
        # type: (...) -> MemoryFS
        from ..memoryfs import MemoryFS

        mem_fs = MemoryFS()
        return mem_fs
