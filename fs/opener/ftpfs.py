# coding: utf-8
"""`FTPFS` opener definition.
"""

from __future__ import absolute_import, print_function, unicode_literals

import typing

from ..errors import CreateFailed
from .base import Opener
from .registry import registry

if typing.TYPE_CHECKING:
    from typing import Text, Union

    from ..ftpfs import FTPFS  # noqa: F401
    from ..subfs import SubFS
    from .parse import ParseResult


@registry.install
class FTPOpener(Opener):
    """`FTPFS` opener."""

    protocols = ["ftp", "ftps"]

    @CreateFailed.catch_all
    def open_fs(
        self,
        fs_url,  # type: Text
        parse_result,  # type: ParseResult
        writeable,  # type: bool
        create,  # type: bool
        cwd,  # type: Text
    ):
        # type: (...) -> Union[FTPFS, SubFS[FTPFS]]
        from ..ftpfs import FTPFS
        from ..subfs import ClosingSubFS

        ftp_host, _, dir_path = parse_result.resource.partition("/")
        ftp_host, _, ftp_port = ftp_host.partition(":")
        ftp_port = int(ftp_port) if ftp_port.isdigit() else 21
        ftp_fs = FTPFS(
            ftp_host,
            port=ftp_port,
            user=parse_result.username,
            passwd=parse_result.password,
            proxy=parse_result.params.get("proxy"),
            timeout=int(parse_result.params.get("timeout", "10")),
            tls=bool(parse_result.protocol == "ftps"),
        )
        if dir_path:
            if create:
                ftp_fs.makedirs(dir_path, recreate=True)
            return ftp_fs.opendir(dir_path, factory=ClosingSubFS)
        else:
            return ftp_fs
