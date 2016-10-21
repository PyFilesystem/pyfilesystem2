"""A collection of functions that operate on filesystems and tools."""

from __future__ import print_function
from __future__ import unicode_literals

from . import constants
from . import errors
from .enums import ResourceType
from .errors import DirectoryNotEmpty
from .errors import ResourceNotFound
from .path import abspath
from .path import dirname
from .path import normpath
from .path import recursepath


def remove_empty(fs, path):
    """
    Remove all empty parents.

    :param fs: A filesystem object.
    :param path: Path to a directory on the filesystem.

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

    :param src_file: File open for reading.
    :type src_file: file object
    :param dst_file: File open for writing.
    :type dst_file: file object
    :param chunk_size: Number of bytes to copy at a time (None to use
        sensible default).
    :returns: Number of bytes copied.
    :rtype: int

    """
    chunk_size = chunk_size or constants.DEFAULT_CHUNK_SIZE
    count = 0
    read = src_file.read
    write = dst_file.write
    chunk = read(chunk_size)
    while chunk:
        write(chunk)
        count += len(chunk)
        chunk = read(chunk_size)
    return count


def get_intermediate_dirs(fs, dir_path):
    """
    Get paths of intermediate directories required to create a new
    directory.

    :param fs: A filesystem object.
    :param dir_path: A path to a new directory on the filesystem.
    :returns: A list of paths.
    :rtype: list

    :raises:

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
