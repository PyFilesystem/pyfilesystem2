# coding: utf-8
"""``AppFS`` opener definition.
"""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import typing

from .base import Opener
from .registry import registry
from .errors import OpenerError

if typing.TYPE_CHECKING:
    from typing import Text, Union
    from .parse import ParseResult
    from ..appfs import _AppFS
    from ..subfs import SubFS


@registry.install
class AppFSOpener(Opener):
    """``AppFS`` opener.
    """

    protocols = ["userdata", "userconf", "sitedata", "siteconf", "usercache", "userlog"]
    _protocol_mapping = None

    def open_fs(
        self,
        fs_url,  # type: Text
        parse_result,  # type: ParseResult
        writeable,  # type: bool
        create,  # type: bool
        cwd,  # type: Text
    ):
        # type: (...) -> Union[_AppFS, SubFS[_AppFS]]

        from ..subfs import ClosingSubFS
        from .. import appfs

        if self._protocol_mapping is None:
            self._protocol_mapping = {
                "userdata": appfs.UserDataFS,
                "userconf": appfs.UserConfigFS,
                "sitedata": appfs.SiteDataFS,
                "siteconf": appfs.SiteConfigFS,
                "usercache": appfs.UserCacheFS,
                "userlog": appfs.UserLogFS,
            }

        fs_class = self._protocol_mapping[parse_result.protocol]
        resource, delim, path = parse_result.resource.partition("/")
        tokens = resource.split(":", 3)
        if len(tokens) == 2:
            appname, author = tokens
            version = None
        elif len(tokens) == 3:
            appname, author, version = tokens
        else:
            raise OpenerError(
                "resource should be <appname>:<author> "
                "or <appname>:<author>:<version>"
            )

        app_fs = fs_class(appname, author=author, version=version, create=create)

        if delim:
            if create:
                app_fs.makedir(path, recreate=True)
            return app_fs.opendir(path, factory=ClosingSubFS)

        return app_fs
