"""Functions for moving files between filesystems.
"""

from __future__ import print_function
from __future__ import unicode_literals

from .copy import copy_dir
from .copy import copy_file
from .opener import manage_fs


def move_fs(src_fs, dst_fs):
    """Move the contents of a filesystem to another filesystem.

    Arguments:
        src_fs (FS or str): Source filesystem (instance or URL).
        dst_fs (FS or str): Destination filesystem (instance or URL).

    """
    move_dir(src_fs, '/', dst_fs, '/')


def move_file(src_fs, src_path, dst_fs, dst_path):
    """Move a file from one filesystem to another.

    Arguments:
        src_fs (FS or str): Source filesystem (instance or URL).
        src_path (str): Path to a file on ``src_fs``.
        dst_fs (FS or str); Destination filesystem (instance or URL).
        dst_path (str): Path to a file on ``dst_fs``.

    """
    with manage_fs(src_fs) as src_fs:
        with manage_fs(dst_fs, create=True) as dst_fs:
            if src_fs is dst_fs:
                # Same filesystem, may be optimized
                src_fs.move(src_path, dst_path, overwrite=True)
            else:
                # Standard copy and delete
                with src_fs.lock(), dst_fs.lock():
                    copy_file(src_fs, src_path, dst_fs, dst_path)
                    src_fs.remove(src_path)


def move_dir(src_fs, src_path, dst_fs, dst_path):
    """Move a directory from one filesystem to another.

    Arguments:
        src_fs (FS or str): Source filesystem (instance or URL).
        src_path (str): Path to a directory on ``src_fs``
        dst_fs (FS or str): Destination filesystem (instance or URL).
        dst_path (str): Path to a directory on ``dst_fs``

    """
    with manage_fs(src_fs) as src_fs:
        with manage_fs(dst_fs, create=True) as dst_fs:
            with src_fs.lock(), dst_fs.lock():
                dst_fs.makedir(dst_path, recreate=True)
                copy_dir(
                    src_fs,
                    src_path,
                    dst_fs,
                    dst_path
                )
                src_fs.removetree(src_path)
