"""

Create a 'mirror' of a filesystem.

"""

from __future__ import print_function
from __future__ import unicode_literals


from .copy import copy_file
from .errors import ResourceNotFound
from .walk import Walker
from .opener import manage_fs


def _compare(info1, info2):
    """
    Compare two (file) info objects and return True if the file should
    be copied, or False if they should not.

    """
    # Check filesize has changed
    if info1.size != info2.size:
        return True
    # Check modified dates
    date1 = info1.modified
    date2 = info2.modified
    return date1 is None or date2 is None or date1 > date2


def mirror(src_fs, dst_fs, walker=None, copy_if_newer=True):
    """
    Mirror files / directories from one filesystem to another.

    :param src_fs: A source filesystem.
    :type src_fs: FS URL or instance.
    :param dst_fs: A destination filesystem.
    :type dst_fs: FS URL or instance.
    :param walker: An optional waler instance.
    :type walker: :class:`~fs.walk.Walker`
    :param bool copy_if_newer: Only copy newer files.

    Mirroring a filesystem will create an exact copy of ``src_fs`` on
    ``dst_fs``, by removing any files / directories on the destination
    that aren't on the source, and copying files that aren't.

    """
    with manage_fs(src_fs, writeable=False) as _src_fs:
        with manage_fs(dst_fs, create=True) as _dst_fs:
            with _src_fs.lock(), _dst_fs.lock():
                return _mirror(
                    _src_fs,
                    _dst_fs,
                    walker=walker,
                    copy_if_newer=copy_if_newer
                )


def _mirror(src_fs, dst_fs, walker=None, copy_if_newer=True):
    walker = walker or Walker()
    walk = walker.walk(src_fs, namespaces=['details'])
    for path, dirs, files in walk:
        try:
            dst = {
                info.name: info
                for info in dst_fs.scandir(path, namespaces=['details'])
            }
        except ResourceNotFound:
            dst_fs.makedir(path)
            dst = {}

        # Copy files
        for _file in files:
            _path = _file.make_path(path)
            dst_file = dst.pop(_file.name, None)
            if dst_file is not None:
                if dst_file.is_dir:
                    # Destination is a directory, remove it
                    dst_fs.removetree(_path)
                else:
                    # Compare file info
                    if copy_if_newer and not _compare(_file, dst_file):
                        continue
            copy_file(src_fs, _path, dst_fs, _path)

        # Make directories
        for _dir in dirs:
            _path = _dir.make_path(path)
            dst_dir = dst.pop(_dir.name, None)
            if dst_dir is not None:
                # Directory name exists on dst
                if not dst_dir.is_dir:
                    # Not a directory, so remove it
                    dst_fs.remove(_path)
            else:
                # Make the directory in dst
                dst_fs.makedir(_path, recreate=True)

        # Remove any remaining resources
        while dst:
            _, info = dst.popitem()
            _path = info.make_path(path)
            if info.is_dir:
                dst_fs.removetree(_path)
            else:
                dst_fs.remove(_path)
