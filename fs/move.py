from __future__ import print_function
from __future__ import unicode_literals

from .copy import copy_dir
from .copy import copy_file
from .path import abspath
from .path import normpath


class MoveError(Exception):
    pass


def move_file(src_fs, src_path, dst_fs, dst_path):
    """
    Move a file from one filesystem to another.

    :param src_fs: Source filesystem.
    :param src_path: Path to a file on ``src_fs``.
    :param dst_fs: Destination filesystem.
    :param dst_fs: Path to a file on ``dst_fs``.

    """
    if src_fs is dst_fs:
        # Same filesystem, may be optimized
        src_fs.move(src_path, dst_path, overwrite=True)
    else:
        # Standard copy and delete
        with src_fs.lock(), dst_fs.lock():
            copy_file(src_fs, src_path, dst_fs, dst_path)
            src_fs.remove(src_path)


def move_dir(src_fs, src_path, dst_fs, dst_path, create=False):
    """
    Move a directory from one filesystem to another.

    :param src_fs: Source filesystem.
    :type src_fs: :class:`fs.base.FS`
    :param src_path: A path to a directory on ``src_fs``.
    :type src_path: str
    :param dst_fs: Destination filesystem.
    :type dst_fs: :class:`fs.base.FS`
    :param dst_path: A path to a directory on ``dst_fs``.
    :param create: If True, create ``dst_path`` if it doesn't exist.
    :type create: bool

    """

    _src_path = abspath(normpath(src_path))
    _dst_path = abspath(normpath(dst_path))

    with src_fs.lock(), dst_fs.lock():
        if create:
            dst_fs.makedir(_dst_path, recreate=True)
        else:
            if not dst_fs.isdir(_dst_path):
                raise MoveError(
                    "'{}' does not exist on {}".format(dst_path, dst_fs)
                )
        copy_dir(
            src_fs,
            src_path,
            dst_fs,
            dst_path
        )
        src_fs.removetree(_src_path)
