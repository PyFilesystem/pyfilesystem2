"""Manage filesystems in temporary locations.

A temporary filesytem is stored in a location defined by your OS
(``/tmp`` on linux). The contents are deleted when the filesystem
is closed.

A `TempFS` is a good way of preparing a directory structure in advance,
that you can later copy. It can also be used as a temporary data store.

"""

from __future__ import print_function, unicode_literals

import typing

import shutil
import six
import tempfile

from . import errors
from .osfs import OSFS

if typing.TYPE_CHECKING:
    from typing import Optional, Text


@six.python_2_unicode_compatible
class TempFS(OSFS):
    """A temporary filesystem on the OS.

    Temporary filesystems are created using the `tempfile.mkdtemp`
    function to obtain a temporary folder in an OS-specific location.
    You can provide an alternative location with the ``temp_dir``
    argument of the constructor.

    Examples:
        Create with the constructor::

            >>> from fs.tempfs import TempFS
            >>> tmp_fs = TempFS()

        Or via an FS URL::

            >>> import fs
            >>> tmp_fs = fs.open_fs("temp://")

        Use a specific identifier for the temporary folder to better
        illustrate its purpose::

            >>> named_tmp_fs = fs.open_fs("temp://local_copy")
            >>> named_tmp_fs = TempFS(identifier="local_copy")

    """

    def __init__(
        self,
        identifier="__tempfs__",  # type: Text
        temp_dir=None,  # type: Optional[Text]
        auto_clean=True,  # type: bool
        ignore_clean_errors=True,  # type: bool
    ):
        # type: (...) -> None
        """Create a new `TempFS` instance.

        Arguments:
            identifier (str): A string to distinguish the directory within
                the OS temp location, used as part of the directory name.
            temp_dir (str, optional): An OS path to your temp directory
                (leave as `None` to auto-detect).
            auto_clean (bool): If `True` (the default), the directory
                contents will be wiped on close.
            ignore_clean_errors (bool): If `True` (the default), any errors
                in the clean process will be suppressed. If `False`, they
                will be raised.

        """
        self.identifier = identifier
        self._auto_clean = auto_clean
        self._ignore_clean_errors = ignore_clean_errors
        self._cleaned = False

        self.identifier = identifier.replace("/", "-")

        self._temp_dir = tempfile.mkdtemp(identifier or "fsTempFS", dir=temp_dir)
        super(TempFS, self).__init__(self._temp_dir)

    def __repr__(self):
        # type: () -> Text
        return "TempFS()"

    def __str__(self):
        # type: () -> Text
        return "<tempfs '{}'>".format(self._temp_dir)

    def close(self):
        # type: () -> None
        """Close the filesystem and release any resources.

        It is important to call this method when you have finished
        working with the filesystem. Some filesystems may not finalize
        changes until they are closed (archives for example). You may
        call this method explicitly (it is safe to call close multiple
        times), or you can use the filesystem as a context manager to
        automatically close.

        Hint:
            Depending on the value of ``auto_clean`` passed when creating
            the `TempFS`, the underlying temporary folder may be removed
            or not.

        Example:
            >>> tmp_fs = TempFS(auto_clean=False)
            >>> syspath = tmp_fs.getsyspath("/")
            >>> tmp_fs.close()
            >>> os.path.exists(syspath)
            True

        """
        if self._auto_clean:
            self.clean()
        super(TempFS, self).close()

    def clean(self):
        # type: () -> None
        """Clean (delete) temporary files created by this filesystem."""
        if self._cleaned:
            return

        try:
            shutil.rmtree(self._temp_dir)
        except Exception as error:
            if not self._ignore_clean_errors:
                raise errors.OperationFailed(
                    msg="failed to remove temporary directory; {}".format(error),
                    exc=error,
                )
        self._cleaned = True
