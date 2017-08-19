# coding: utf-8
"""Defines the MemOpener."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

from .base import Opener
from .errors import OpenerError
from .. import appfs


class AppFSOpener(Opener):

    protocols = [
        'userdata',
        'userconf',
        'sitedata',
        'siteconf',
        'usercache',
        'userlog'
    ]

    _protocol_mapping = {
        'userdata': appfs.UserDataFS,
        'userconf': appfs.UserConfigFS,
        'sitedata': appfs.SiteDataFS,
        'siteconf': appfs.SiteConfigFS,
        'usercache': appfs.UserCacheFS,
        'userlog': appfs.UserLogFS
    }

    def open_fs(self, fs_url, parse_result, writeable, create, cwd):
        fs_class = self._protocol_mapping[parse_result.protocol]

        tokens = parse_result.resource.split(':', 3)
        if len(tokens) == 2:
            appname, author = tokens
            version = None
        elif len(tokens) == 3:
            appname, author, version = tokens
        else:
            raise OpenerError(
                'resource should be <appname>:<author> '
                'or <appname>:<author>:<version>'
            )

        fs_instance = fs_class(
            appname,
            author=author,
            version=version,
            create=create
        )
        return fs_instance

