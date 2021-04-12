"""Functions for moving files between filesystems.
"""

from __future__ import print_function
from __future__ import unicode_literals

import typing

from .copy import copy_dir
from .copy import copy_file
from .opener import manage_fs

if typing.TYPE_CHECKING:
    from .base import FS
    from typing import Text, Union


def move_fs(
    src_fs,  # type: Union[Text, FS]
    dst_fs,  # type:Union[Text, FS]
    workers=0,  # type: int
    preserve_time=False,  # type: bool
):
    # type: (...) -> None
    """Move the contents of a filesystem to another filesystem.

    Arguments:
        src_fs (FS or str): Source filesystem (instance or URL).
        dst_fs (FS or str): Destination filesystem (instance or URL).
        workers (int): Use `worker` threads to copy data, or ``0`` (default) for
            a single-threaded copy.
        preserve_time (bool): If `True`, try to preserve mtime of the
            resources (defaults to `False`).

    """
    move_dir(src_fs, "/", dst_fs, "/", workers=workers, preserve_time=preserve_time)


def move_file(
    src_fs,  # type: Union[Text, FS]
    src_path,  # type: Text
    dst_fs,  # type: Union[Text, FS]
    dst_path,  # type: Text
    preserve_time=False,  # type: bool
):
    # type: (...) -> None
    """Move a file from one filesystem to another.

    Arguments:
        src_fs (FS or str): Source filesystem (instance or URL).
        src_path (str): Path to a file on ``src_fs``.
        dst_fs (FS or str): Destination filesystem (instance or URL).
        dst_path (str): Path to a file on ``dst_fs``.
        preserve_time (bool): If `True`, try to preserve mtime of the
            resources (defaults to `False`).

    """
    with manage_fs(src_fs) as _src_fs:
        with manage_fs(dst_fs, create=True) as _dst_fs:
            if _src_fs is _dst_fs:
                # Same filesystem, may be optimized
                _src_fs.move(
                    src_path, dst_path, overwrite=True, preserve_time=preserve_time
                )
            else:
                # Standard copy and delete
                with _src_fs.lock(), _dst_fs.lock():
                    copy_file(
                        _src_fs,
                        src_path,
                        _dst_fs,
                        dst_path,
                        preserve_time=preserve_time,
                    )
                    _src_fs.remove(src_path)


def move_dir(
    src_fs,  # type: Union[Text, FS]
    src_path,  # type: Text
    dst_fs,  # type: Union[Text, FS]
    dst_path,  # type: Text
    workers=0,  # type: int
    preserve_time=False,  # type: bool
):
    # type: (...) -> None
    """Move a directory from one filesystem to another.

    Arguments:
        src_fs (FS or str): Source filesystem (instance or URL).
        src_path (str): Path to a directory on ``src_fs``
        dst_fs (FS or str): Destination filesystem (instance or URL).
        dst_path (str): Path to a directory on ``dst_fs``.
        workers (int): Use ``worker`` threads to copy data, or ``0``
            (default) for a single-threaded copy.
        preserve_time (bool): If `True`, try to preserve mtime of the
            resources (defaults to `False`).

    """

    def src():
        return manage_fs(src_fs, writeable=False)

    def dst():
        return manage_fs(dst_fs, create=True)

    with src() as _src_fs, dst() as _dst_fs:
        with _src_fs.lock(), _dst_fs.lock():
            _dst_fs.makedir(dst_path, recreate=True)
            copy_dir(
                src_fs,
                src_path,
                dst_fs,
                dst_path,
                workers=workers,
                preserve_time=preserve_time,
            )
            _src_fs.removetree(src_path)
