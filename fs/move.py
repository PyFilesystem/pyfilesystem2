"""

Functions for moving files between filesystems.

"""

from __future__ import print_function
from __future__ import unicode_literals

from .copy import copy_dir
from .copy import copy_file
from .opener import manage_fs


def move_fs(src_fs, dst_fs):
    """
    Move the contents of a filesystem to another filesystem.

    :param src_fs: Source filesystem.
    :type src_fs: FS URL or instance
    :param dst_fs: Destination filesystem.
    :type dst_fs: FS URL or instance

    """
    move_dir(src_fs, '/', dst_fs, '/')


def move_file(src_fs, src_path, dst_fs, dst_path):
    """
    Move a file from one filesystem to another.

    :param src_fs: Source filesystem.
    :type src_fs: FS URL or instance
    :param src_path: Path to a file on ``src_fs``.
    :type src_path: str
    :param dst_fs: Destination filesystem.
    :type dst_fs: FS URL or instance
    :param dst_fs: Path to a file on ``dst_fs``.
    :type dst_fs: str

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
    """
    Move a directory from one filesystem to another.

    :param src_fs: Source filesystem.
    :type src_fs: FS URL or instance
    :param src_path: A path to a directory on ``src_fs``.
    :type src_path: str
    :param dst_fs: Destination filesystem.
    :type dst_fs: FS URL or instance
    :param str dst_path: A path to a directory on ``dst_fs``.

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
