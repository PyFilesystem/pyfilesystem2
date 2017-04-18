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
from .errors import FSError


def copy_fs(src_fs, dst_fs, walker=None, on_copy=None):
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
    :param on_copy: A function callback called after a single file copy
        is executed.
    :type on_copy: Function, with signature ``(src_fs, src_path, dst_fs,
        dst_path)``.
    """
    return copy_dir(src_fs, '/', dst_fs, '/',
                    walker=walker, on_copy=on_copy)


def copy_fs_if_newer(src_fs, dst_fs, walker=None, on_copy=None):
    """
    Copy the contents of one filesystem to another. If both source and
    destination files exist, the copy is executed only if the source
    file is newer than the destination file. In case modification times
    of source or destination files are not available, copy file is
    always executed.

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
    :param on_copy: A function callback called after a single file copy
        is executed.
    :type on_copy: Function, with signature ``(src_fs, src_path, dst_fs,
        dst_path)``.
    """
    return copy_dir_if_newer(src_fs, '/', dst_fs, '/',
                             walker=walker, on_copy=on_copy)


def _source_is_newer(src_fs, src_path, dst_fs, dst_path):
    """
       Determine if source file is newer than destination file.

       :param src_fs: Source filesystem.
       :type src_fs: :type src_fs: FS URL or instance
       :param src_path: A path to a directory on ``src_fs``.
       :type src_path: str
       :param dst_fs: Destination filesystem.
       :type dst_fs: FS URL or instance
       :returns: True if source file is newer than destination file or
            file modification time cannot be determined. False otherwise.
       """
    try:
        if dst_fs.exists(dst_path):
            namespace = ('details', 'modified')
            src_modified = src_fs.getinfo(src_path, namespace).modified
            if src_modified is not None:
                dst_modified = dst_fs.getinfo(dst_path, namespace).modified
                return dst_modified is None or src_modified > dst_modified
        return True
    except FSError:  # pragma: nocover
        #todo: should log something here
        return True

def copy_file(src_fs, src_path, dst_fs, dst_path):
    """
    Copy a file from one filesystem to another. If the destination
    exists, and is a file, it will be first truncated.

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
                # Same filesystem, so we can do a potentially optimized
                # copy
                src_fs.copy(src_path, dst_path, overwrite=True)
            else:
                # Standard copy
                with src_fs.lock(), dst_fs.lock():
                    with src_fs.open(src_path, 'rb') as read_file:
                        # There may be an optimized copy available on
                        # dst_fs
                        dst_fs.setbinfile(dst_path, read_file)


def copy_file_if_newer(src_fs, src_path, dst_fs, dst_path):
    """
    Copy a file from one filesystem to another. If the destination
    exists, and is a file, it will be first truncated. If both source
    and destination files exist, the copy is executed only if the source
    file is newer than the destination file. In case modification times
    of source or destination files are not available, copy is always
    executed.

    :param src_fs: Source filesystem.
    :type src_fs: FS URL or instance
    :param src_path: Path to a file on ``src_fs``.
    :type src_path: str
    :param dst_fs: Destination filesystem.
    :type dst_fs: FS URL or instance
    :param dst_path: Path to a file on ``dst_fs``.
    :type dst_path: str
    :returns: True if the file copy was executed, False otherwise.

    """
    with manage_fs(src_fs, writeable=False) as src_fs:
        with manage_fs(dst_fs, create=True) as dst_fs:
            if src_fs is dst_fs:
                # Same filesystem, so we can do a potentially optimized
                # copy
                if _source_is_newer(src_fs, src_path, dst_fs, dst_path):
                    src_fs.copy(src_path, dst_path, overwrite=True)
                    return True
                else:
                    return False
            else:
                # Standard copy
                with src_fs.lock(), dst_fs.lock():
                    if _source_is_newer(src_fs, src_path,
                                        dst_fs, dst_path):
                        with src_fs.open(src_path, 'rb') as read_file:
                            # There may be an optimized copy available
                            # on dst_fs
                            dst_fs.setbinfile(dst_path, read_file)
                            return True
                    else:
                        return False



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


def copy_dir(src_fs, src_path, dst_fs, dst_path,
             walker=None, on_copy=None):
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
    :param on_copy: A function callback called after a single file copy
        is executed.
    :type on_copy: Function, with signature ``(src_fs, src_path, dst_fs,
        dst_path)``.

    """
    on_copy = on_copy or (lambda *args: None)
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
                        src_path = info.make_path(dir_path)
                        dst_path = info.make_path(copy_path)
                        copy_file(
                            src_fs,
                            src_path,
                            dst_fs,
                            dst_path
                        )
                        on_copy(src_fs, src_path, dst_fs, dst_path)


def copy_dir_if_newer(src_fs, src_path, dst_fs, dst_path,
                      walker=None, on_copy=None):
    """
    Copy a directory from one filesystem to another. If both source and
    destination files exist, the copy is executed only if the source
    file is newer than the destination file. In case modification times
    of source or destination files are not available, copy is always
    executed.

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
    :param on_copy: A function callback called after a single file copy
        is executed.
    :type on_copy: Function, with signature ``(src_fs, src_path, dst_fs,
        dst_path)``.

    """
    on_copy = on_copy or (lambda *args: None)
    walker = walker or Walker()
    _src_path = abspath(normpath(src_path))
    _dst_path = abspath(normpath(dst_path))
    with manage_fs(src_fs, writeable=False) as src_fs:
        with manage_fs(dst_fs, create=True) as dst_fs:
            with src_fs.lock(), dst_fs.lock():
                dst_fs.makedir(_dst_path, recreate=True)
                namespace = ('details', 'modified')
                dst_state = {
                    path: info
                    for path, info in walker.info(dst_fs, _dst_path, namespace)
                    if info.is_file
                }
                src_state = [
                    (path, info)
                    for path, info in walker.info(src_fs, _src_path, namespace)
                ]
                for dir_path, copy_info in src_state:
                    copy_path = combine(
                        _dst_path,
                        frombase(_src_path, dir_path)
                    )
                    if copy_info.is_dir:
                        dst_fs.makedir(copy_path, recreate=True)
                    elif copy_info.is_file:
                        # dst file is present, try to figure out if copy
                        # is necessary
                        src_modified = copy_info.modified
                        do_copy = (
                            dir_path not in dst_state or
                            src_modified is None or
                            dst_state[dir_path].modified is None or
                            src_modified > dst_state[dir_path].modified
                        )
                        if do_copy:
                            copy_file(src_fs, dir_path, dst_fs, copy_path)
                            on_copy(src_fs, dir_path, dst_fs, copy_path)

