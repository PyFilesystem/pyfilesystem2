"""Functions for moving files between filesystems.
"""

from __future__ import print_function, unicode_literals

import typing

import os

from ._pathcompat import commonpath
from .copy import copy_dir, copy_file
from .error_tools import convert_os_errors
from .errors import DirectoryExpected, FSError, IllegalDestination, ResourceNotFound
from .opener import manage_fs
from .osfs import OSFS
from .path import frombase, isbase

if typing.TYPE_CHECKING:
    from typing import Text, Union

    from .base import FS


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
    cleanup_dst_on_error=True,  # type: bool
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
        cleanup_dst_on_error (bool): If `True`, tries to delete the file copied to
            ``dst_fs`` if deleting the file from ``src_fs`` fails (defaults to `True`).

    """
    with manage_fs(src_fs, writeable=True) as _src_fs:
        with manage_fs(dst_fs, writeable=True, create=True) as _dst_fs:
            if _src_fs is _dst_fs:
                # Same filesystem, may be optimized
                _src_fs.move(
                    src_path, dst_path, overwrite=True, preserve_time=preserve_time
                )
                return

            if _src_fs.hassyspath(src_path) and _dst_fs.hassyspath(dst_path):
                # if both filesystems have a syspath we create a new OSFS from a
                # common parent folder and use it to move the file.
                try:
                    src_syspath = _src_fs.getsyspath(src_path)
                    dst_syspath = _dst_fs.getsyspath(dst_path)
                    common = commonpath([src_syspath, dst_syspath])
                    if common:
                        rel_src = frombase(common, src_syspath)
                        rel_dst = frombase(common, dst_syspath)
                        with _src_fs.lock(), _dst_fs.lock():
                            with OSFS(common) as base:
                                base.move(
                                    rel_src,
                                    rel_dst,
                                    overwrite=True,
                                    preserve_time=preserve_time,
                                )
                                return  # optimization worked, exit early
                except ValueError:
                    # This is raised if we cannot find a common base folder.
                    # In this case just fall through to the standard method.
                    pass

            # Standard copy and delete
            with _src_fs.lock(), _dst_fs.lock():
                copy_file(
                    _src_fs,
                    src_path,
                    _dst_fs,
                    dst_path,
                    preserve_time=preserve_time,
                )
                try:
                    _src_fs.remove(src_path)
                except FSError as e:
                    # if the source cannot be removed we delete the copy on the
                    # destination
                    if cleanup_dst_on_error:
                        _dst_fs.remove(dst_path)
                    raise e


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

    Raises:
        fs.errors.ResourceNotFound: if ``src_path`` does not exist on `src_fs`
        fs.errors.DirectoryExpected: if ``src_path`` or one of its
            ancestors is not a directory.
        fs.errors.IllegalDestination: when moving a folder into itself

    """
    with manage_fs(src_fs, writeable=True) as _src_fs:
        with manage_fs(dst_fs, writeable=True, create=True) as _dst_fs:
            if not _src_fs.exists(src_path):
                raise ResourceNotFound(src_path)
            if not _src_fs.isdir(src_path):
                raise DirectoryExpected(src_path)

            # if both filesystems have a syspath we use `os.rename` to move the folder
            if _src_fs.hassyspath(src_path) and _dst_fs.hassyspath(dst_path):
                src_syspath = _src_fs.getsyspath(src_path)
                dst_syspath = _dst_fs.getsyspath(dst_path)
                # recheck if the move operation is legal using the syspaths
                if isbase(src_syspath, dst_syspath):
                    raise IllegalDestination(dst_path)
                with _src_fs.lock(), _dst_fs.lock():
                    with convert_os_errors("move_dir", dst_path, directory=True):
                        if _dst_fs.exists(dst_path):
                            os.rmdir(dst_syspath)
                        os.rename(src_syspath, dst_syspath)
                        # recreate the root dir if it has been renamed
                        _src_fs.makedir("/", recreate=True)
                    return  # optimization worked, exit early

            # standard copy then delete
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
