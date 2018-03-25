"""Manage a directory in a *parent* filesystem.
"""

from __future__ import print_function
from __future__ import unicode_literals

import typing

import six

from .wrapfs import WrapFS
from .path import abspath, join, normpath, relpath

if typing.TYPE_CHECKING:
    from typing import Text, Tuple
    from .base import FS


@six.python_2_unicode_compatible
class SubFS(WrapFS):
    """A sub-directory on another filesystem.

    A SubFS is a filesystem object that maps to a sub-directory of
    another filesystem. This is the object that is returned by
    `~fs.base.FS.opendir`.

    """

    def __init__(self, parent_fs, path):
        # type: (FS, Text) -> None
        super(SubFS, self).__init__(parent_fs)
        self._sub_dir = abspath(normpath(path))

    def __repr__(self):
        # type: () -> Text
        return "{}({!r}, {!r})".format(
            self.__class__.__name__,
            self._wrap_fs,
            self._sub_dir
        )

    def __str__(self):
        # type: () -> Text
        return "{parent}{dir}".format(
            parent=self._wrap_fs,
            dir=self._sub_dir
        )

    def delegate_fs(self):
        # type: () -> FS
        return self._wrap_fs

    def delegate_path(self, path):
        # type: (Text) -> Tuple[FS, Text]
        _path = join(self._sub_dir, relpath(normpath(path)))
        return self._wrap_fs, _path


class ClosingSubFS(SubFS):
    """A version of `SubFS` which closes its parent when closed.
    """

    def close(self):
        # type: () -> None
        self.delegate_fs().close()
        super(ClosingSubFS, self).close()
