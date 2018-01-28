"""Function for *mirroring* a filesystem.

Mirroring will create a copy of a source filesystem on a destination
filesystem. If there are no files on the destination, then mirroring
is simply a straight copy. If there are any files or directories on the
destination they may be deleted or modified to match the source.

In order to avoid redundant copying of files, `mirror` can compare
timestamps, and only copy files with a newer modified date. This
timestamp comparison is only done if the file sizes are different.

This scheme will work if you have mirrored a directory previously, and
you would like to copy any changes. Otherwise you should set the
``copy_if_newer`` parameter to `False` to guarantee an exact copy, at
the expense of potentially copying extra files.

"""

from __future__ import print_function
from __future__ import unicode_literals


from .copy import copy_file_internal
from .errors import ResourceNotFound
from .walk import Walker
from .opener import manage_fs


def _compare(info1, info2):
    """Compare two `Info` objects to see if they should be copied.

    Returns:
        bool: `True` if the `Info` are different in size or mtime.

    """
    # Check filesize has changed
    if info1.size != info2.size:
        return True
    # Check modified dates
    date1 = info1.modified
    date2 = info2.modified
    return date1 is None or date2 is None or date1 > date2


def mirror(src_fs, dst_fs, walker=None, copy_if_newer=True):
    """Mirror files / directories from one filesystem to another.

    Mirroring a filesystem will create an exact copy of ``src_fs`` on
    ``dst_fs``, by removing any files / directories on the destination
    that aren't on the source, and copying files that aren't.

    Arguments:
        src_fs (FS or str): Source filesystem (URL or instance).
        dst_fs (FS or str): Destination filesystem (URL or instance).
        walker (~fs.walk.Walker, optional): An optional walker instance.
        copy_if_newer (bool, optional): Only copy newer files (the default).

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
            copy_file_internal(src_fs, _path, dst_fs, _path)

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
