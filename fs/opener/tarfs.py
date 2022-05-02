# coding: utf-8
"""`TarFS` opener definition.
"""

from __future__ import absolute_import, print_function, unicode_literals

import typing

from .base import Opener
from .errors import NotWriteable
from .registry import registry

if typing.TYPE_CHECKING:
    from typing import Text

    from ..tarfs import TarFS  # noqa: F401
    from .parse import ParseResult


@registry.install
class TarOpener(Opener):
    """`TarFS` opener."""

    protocols = ["tar"]

    def open_fs(
        self,
        fs_url,  # type: Text
        parse_result,  # type: ParseResult
        writeable,  # type: bool
        create,  # type: bool
        cwd,  # type: Text
    ):
        # type: (...) -> TarFS
        from ..tarfs import TarFS

        if not create and writeable:
            raise NotWriteable("Unable to open existing TAR file for writing")
        tar_fs = TarFS(parse_result.resource, write=create)
        return tar_fs
