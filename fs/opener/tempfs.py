# coding: utf-8
"""`TempFS` opener definition.
"""

from __future__ import absolute_import, print_function, unicode_literals

import typing

from .base import Opener
from .registry import registry

if typing.TYPE_CHECKING:
    from typing import Text

    from ..tempfs import TempFS  # noqa: F401
    from .parse import ParseResult


@registry.install
class TempOpener(Opener):
    """`TempFS` opener."""

    protocols = ["temp"]

    def open_fs(
        self,
        fs_url,  # type: Text
        parse_result,  # type: ParseResult
        writeable,  # type: bool
        create,  # type: bool
        cwd,  # type: Text
    ):
        # type: (...) -> TempFS
        from ..tempfs import TempFS

        temp_fs = TempFS(identifier=parse_result.resource)
        return temp_fs
