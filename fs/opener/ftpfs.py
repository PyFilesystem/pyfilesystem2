# coding: utf-8
"""Defines the FTPOpener."""

from ._base import Opener
from ._registry import registry

@registry.install
class FTPOpener(Opener):
    protocols = ['ftp']

    def open_fs(self, fs_url, parse_result, writeable, create, cwd):
        from ..ftpfs import FTPFS
        ftp_host, _, dir_path = parse_result.resource.partition('/')
        ftp_host, _, ftp_port = ftp_host.partition(':')
        ftp_port = int(ftp_port) if ftp_port.isdigit() else 21
        ftp_fs = FTPFS(
            ftp_host,
            port=ftp_port,
            user=parse_result.username,
            passwd=parse_result.password,
        )
        ftp_fs = (
            ftp_fs.opendir(dir_path)
            if dir_path else
            ftp_fs
        )
        return ftp_fs
