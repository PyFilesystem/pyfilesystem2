"""
fs.mirror
=========

Utilities to mirror file structures.

"""

from __future__ import print_function
from __future__ import unicode_literals


from .copy import copy_file
from .walk import Walker
from .opener import manage_fs


def _compare(info1, info2, default=True):
    """
    Compare two (file) info objects and return True if the file should
    be copied, or False if they are the same.

    """
    # Check filesize has changed
    if info1.size != info2.size:
        return True
    # Check modified dates
    date1 = info1.modified
    date2 = info2.modified
    if date1 is None or date2 is None:
        # If either FS doesn't support modified, then return default
        return default
    if date1 != date2:
        return True
    return False


def mirror(src_fs, dst_fs, walker=None, compare_modified=True):
    with manage_fs(src_fs, writeable=False) as _src_fs:
        with manage_fs(dst_fs, create=True) as _dst_fs:
            return _mirror(
                _src_fs,
                _dst_fs,
                walker=walker,
                compare_modified=compare_modified
            )


def _mirror(src_fs, dst_fs, walker=None, compare_modified=True):
    walker = walker or Walker()
    walk = walker.walk(src_fs, namespaces=['details'])
    for path, dirs, files in walk:
        dst = {
            info.name: info
            for info in dst_fs.scandir(path, namespace=['details'])
        }

        # Copy files
        for file in files:
            _path = file.make_path(path)
            dst_file = dst.pop(file.name)
            if dst_file is not None:
                if dst_file.is_dir:
                    # Destination is a directory, remove it
                    dst_fs.removetree(_path)
                else:
                    # Compare file info
                    if compare_modified and not _compare(file, dst_file):
                        continue
            copy_file(src_fs, _path, dst_fs, _path)

        # Make directories
        for dir_ in dirs:
            _path = dir_.make_path(path)
            dst_dir = dst.pop(dir_.name)
            if dst_dir is not None:
                # Directory name exists on dst
                if not dst_dir.is_dir:
                    # Not a directory, so remove it
                    dst_fs.remove(dir_.make_path)
            else:
                # Make the directory in dst
                dst_fs.makedir(_path, recreate=True)

        # Remove any remaining resources
        while dst:
            _name, info = dst.popitem()
            _path = info.make_path(path)
            if info.is_dir:
                dst_fs.removetree(_path)
            else:
                dst_fs.remove(_path)
