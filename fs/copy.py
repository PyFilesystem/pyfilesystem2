"""

Functions for copying resources *between* filesystem.

"""

from __future__ import print_function
from __future__ import unicode_literals

from .walk import Walker
from .opener import manage_fs
from .path import abspath
from .path import combine
from .path import frombase
from .path import normpath


def copy_fs(src_fs, dst_fs, walker=None):
    """
    Copy the contents of one filesystem to another.

    :param src_fs: Source filesystem.
    :type src_fs: :type src_fs: FS URL or instance
    :param src_path: A path to a directory on ``src_fs``.
    :type src_path: str
    :param dst_fs: Destination filesystem.
    :type dst_fs: FS URL or instance
    :param walker: A walker object that will be used to scan for files
        in ``src_fs``. Set this if you only want to consider a sub-set
        of the resources in ``src_fs``.
    :type walker: :class:`~fs.walk.Walker`

    """
    copy_dir(src_fs, '/', dst_fs, '/', walker=walker)


def copy_file(src_fs, src_path, dst_fs, dst_path):
    """
    Copy a file from one filesystem to another.

    If the destination exists, and is a file, it will be first
    truncated.

    :param src_fs: Source filesystem.
    :type src_fs: FS URL or instance
    :param src_path: Path to a file on ``src_fs``.
    :type src_path: str
    :param dst_fs: Destination filesystem.
    :type dst_fs: FS URL or instance
    :param dst_path: Path to a file on ``dst_fs``.
    :type dst_path: str

    """
    with manage_fs(src_fs, writeable=False) as src_fs:
        with manage_fs(dst_fs, create=True) as dst_fs:
            if src_fs is dst_fs:
                # Same filesystem, so we can do a potentially optimized copy
                src_fs.copy(src_path, dst_path, overwrite=True)
            else:
                # Standard copy
                with src_fs.lock(), dst_fs.lock():
                    with src_fs.open(src_path, 'rb') as read_file:
                        # There may be an optimized copy available on dst_fs
                        dst_fs.setbinfile(dst_path, read_file)


def copy_structure(src_fs, dst_fs, walker=None):
    """
    Copy directories (but not files) from ``src_fs`` to ``dst_fs``.

    :param src_fs: Source filesystem.
    :type src_fs: FS URL or instance
    :param dst_fs: Destination filesystem.
    :type dst_fs: FS URL or instance
    :param walker: A walker object that will be used to scan for files
        in ``src_fs``. Set this if you only want to consider a sub-set
        of the resources in ``src_fs``.
    :type walker: :class:`~fs.walk.Walker`

    """
    walker = walker or Walker()
    with manage_fs(src_fs, writeable=False) as src_fs:
        with manage_fs(dst_fs, create=True) as dst_fs:
            with src_fs.lock(), dst_fs.lock():
                for dir_path in walker.dirs(src_fs):
                    dst_fs.makedir(dir_path, recreate=True)


def copy_dir(src_fs, src_path, dst_fs, dst_path, walker=None):
    """
    Copy a directory from one filesystem to another.

    :param src_fs: Source filesystem.
    :type src_fs: FS URL or instance
    :param src_path: A path to a directory on ``src_fs``.
    :type src_path: str
    :param dst_fs: Destination filesystem.
    :type dst_fs: FS URL or instance
    :param str dst_path: A path to a directory on ``dst_fs``.
    :param walker: A walker object that will be used to scan for files
        in ``src_fs``. Set this if you only want to consider a sub-set
        of the resources in ``src_fs``.
    :type walker: :class:`~fs.walk.Walker`

    """

    walker = walker or Walker()
    _src_path = abspath(normpath(src_path))
    _dst_path = abspath(normpath(dst_path))

    with manage_fs(src_fs, writeable=False) as src_fs:
        with manage_fs(dst_fs, create=True) as dst_fs:
            with src_fs.lock(), dst_fs.lock():
                dst_fs.makedir(_dst_path, recreate=True)
                for dir_path, dirs, files in walker.walk(src_fs, _src_path):
                    copy_path = combine(
                        _dst_path,
                        frombase(_src_path, dir_path)
                    )
                    for info in dirs:
                        dst_fs.makedir(
                            info.make_path(copy_path),
                            recreate=True
                        )
                    for info in files:
                        copy_file(
                            src_fs,
                            info.make_path(dir_path),
                            dst_fs,
                            info.make_path(copy_path)
                        )
