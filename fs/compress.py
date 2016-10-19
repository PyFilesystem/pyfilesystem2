from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

from datetime import datetime
import time
import zipfile

import six

from .path import relpath
from .errors import NoSysPath
from .walk import Walker


def write_zip(src_fs,
              file,
              compression=zipfile.ZIP_DEFLATED,
              encoding="utf-8",
              walker=None):
    """
    Write a filesystem to a zip file.

    :param file: Destination file, may be a file name or an open file
        object.
    :type file: str or file-like.
    :param compression: Compression to use (one of the constants defined
        in the zipfile module in the stdlib).
    :type compression: str
    :param encoding: The encoding to use for filenames. The default is
        ``"utf-8"``, use ``"CP437"`` if compatibility with WinZip is
        desired.
    :type encoding: str
    :param walker: A :class:`fs.walk.Walker` instance, or None to use
        default walker.
    :type walker: walker or None

    """
    _zip = zipfile.ZipFile(
        file,
        mode="w",
        compression=compression,
        allowZip64=True
    )
    walker = walker or Walker()
    with _zip:
        gen_walk = walker.walk_info(src_fs, namespaces=["details", "stat"])
        for path, info in gen_walk:
            # Zip names must be relative, directory names must end
            # with a slash.
            zip_name = relpath(path + '/' if info.is_dir else path)
            if not six.PY3:
                # Python2 expects bytes filenames
                zip_name = zip_name.encode(encoding, 'replace')

            if info.has_namespace('stat'):
                # If the file has a stat namespace, get the
                # zip time directory from the stat structure
                st_mtime = info.get('stat', 'st_mtime', None)
                _mtime = time.localtime(st_mtime)
                zip_time = _mtime[0:6]
            else:
                # Otherwise, use the modified time from details
                # namespace.
                mt = info.modified or datetime.utcnow()
                zip_time = (
                    mt.year, mt.month, mt.day,
                    mt.hour, mt.minute, mt.second
                )
            zip_info = zipfile.ZipInfo(zip_name, zip_time)

            if info.is_dir:
                # This is how to record directories with zipfile
                _zip.writestr(zip_info, b'')
            else:
                # Get a syspath if possible
                try:
                    sys_path = src_fs.getsyspath(path)
                except NoSysPath:
                    # Write from bytes
                    _zip.writestr(
                        zip_info,
                        src_fs.getbytes(path)
                    )
                else:
                    # Write from a file which is (presumably)
                    # more memory efficient
                    _zip.write(sys_path, zip_name)
