# coding: utf-8
"""`ZipFS` opener definition.
"""

from __future__ import absolute_import, print_function, unicode_literals

import typing

from .base import Opener
from .errors import NotWriteable
from .registry import registry

if typing.TYPE_CHECKING:
    from typing import Text

    from ..zipfs import ZipFS  # noqa: F401
    from .parse import ParseResult


@registry.install
class ZipOpener(Opener):
    """`ZipFS` opener."""

    protocols = ["zip"]

    def open_fs(
        self,
        fs_url,  # type: Text
        parse_result,  # type: ParseResult
        writeable,  # type: bool
        create,  # type: bool
        cwd,  # type: Text
    ):
        # type: (...) -> ZipFS
        from ..zipfs import ZipFS

        if not create and writeable:
            raise NotWriteable("Unable to open existing ZIP file for writing")
        zip_fs = ZipFS(parse_result.resource, write=create)
        return zip_fs
