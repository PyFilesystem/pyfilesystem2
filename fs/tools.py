"""
A collection of functions that operate on filesystems and tools.

"""

from __future__ import print_function
from __future__ import unicode_literals

import io

from . import errors
from .errors import DirectoryNotEmpty
from .errors import ResourceNotFound
from .path import abspath
from .path import dirname
from .path import normpath
from .path import recursepath


def remove_empty(fs, path):
    """
    Remove all empty parents.

    :param fs: A FS object.
    :param str path: Path to a directory on the filesystem.

    """
    path = abspath(normpath(path))
    try:
        while path not in ('', '/'):
            fs.removedir(path)
            path = dirname(path)
    except DirectoryNotEmpty:
        pass


def copy_file_data(src_file, dst_file, chunk_size=None):
    """
    Copy data from one file object to another.

    :param file-like src_file: File open for reading.
    :param file-like dst_file: File open for writing.
    :param int chunk_size: Number of bytes to copy at a time (or
        ``None`` to use sensible default).

    """
    chunk_size = chunk_size or io.DEFAULT_BUFFER_SIZE
    read = src_file.read
    write = dst_file.write
    # The 'or None' is so that it works with binary and text files
    for chunk in iter(lambda: read(chunk_size) or None, None):
        write(chunk)


def get_intermediate_dirs(fs, dir_path):
    """
    Get paths of intermediate directories required to create a new
    directory.

    :param fs: A FS object.
    :param str dir_path: A path to a new directory on the filesystem.
    :returns: A list of paths.
    :rtype: list

    :raises `fs.errors.DirectoryExpected`: If a path component
        references a file and not a directory.

    """
    intermediates = []
    with fs.lock():
        for path in recursepath(abspath(dir_path), reverse=True):
            try:
                resource = fs.getinfo(path)
            except ResourceNotFound:
                intermediates.append(abspath(path))
            else:
                if resource.is_dir:
                    break
                raise errors.DirectoryExpected(dir_path)
    return intermediates[::-1][:-1]
