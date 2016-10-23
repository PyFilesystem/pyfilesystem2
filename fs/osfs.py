
from __future__ import print_function
from __future__ import unicode_literals

import errno
import grp
import io
import logging
import os
import platform
import pwd
import stat
import sys

import six

try:
    from os import scandir
except ImportError:
    from scandir import scandir

from . import errors
from .base import FS
from .enums import ResourceType
from .info import Info
from .path import abspath, basename, normpath
from .permissions import Permissions
from .error_tools import convert_os_errors
from .mode import validate_openbin_mode, validate_open_mode


log = logging.getLogger('fs.osfs')


_WINDOWS_PLATFORM = platform.system() == 'Windows'


@six.python_2_unicode_compatible
class OSFS(FS):
    """
    Create an OSFS.

    :param root_path: An OS path to the location on your HD you
        wish to manage.
    :type root_path: str
    :param create: Set to True to create the directory if it
        does not already exist.
    :type create: bool
    :param encoding: The encoding to use for paths (or ``None``) to
        autodetect.
    :type encoding: str


    """

    def __init__(self,
                 root_path,
                 create=False,
                 create_mode=0o777,
                 encoding=None):
        """Create an OSFS instance."""

        super(OSFS, self).__init__()
        self.encoding = encoding or sys.getfilesystemencoding()

        _root_path = os.path.expanduser(os.path.expandvars(root_path))
        _root_path = os.path.normpath(os.path.abspath(root_path))
        self.root_path = _root_path

        if create:
            try:
                if not os.path.isdir(_root_path):
                    os.makedirs(_root_path, mode=create_mode)
            except OSError as e:
                raise errors.CreateFailed(
                    'unable to create {} ({})'.format(root_path, e)
                )

        _meta = self._meta = {
            'case_insensitive': os.path.normcase('Aa') != 'aa',
            'network': False,
            'read_only': False,
            'supports_rename': True,
            'thread_safe': True,
            'unicode_paths': os.path.supports_unicode_filenames,
            'virtual': False,
        }

        if _WINDOWS_PLATFORM:  # pragma: nocover
            _meta["invalid_path_chars"] =\
                ''.join(six.unichr(n) for n in xrange(31)) + '\\:*?"<>|'
        else:
            _meta["invalid_path_chars"] = '\0'

        if 'PC_PATH_MAX' in os.pathconf_names:
            _meta['max_sys_path_length'] =\
                os.pathconf(root_path, os.pathconf_names['PC_PATH_MAX'])

    def __repr__(self):
        return "OSFS({!r}, encoding={!r})".format(self.root_path,
                                                  self.encoding)

    def __str__(self):
        fmt = "<osfs '{}'>"
        return fmt.format(self.root_path)

    def _to_sys_path(self, path):
        """Convert a FS path to a path on the OS."""
        path = normpath(path).lstrip('/').replace('/', os.sep)
        sys_path = os.path.join(self.root_path, path)
        return sys_path

    @classmethod
    def _make_details_from_stat(cls, stat):
        """Make an info dict from a stat_result object."""
        details = {
            '_write': ['accessed', 'modified'],
            'accessed': stat.st_atime,
            'modified': stat.st_mtime,
            'size': stat.st_size,
            'type': int(cls._get_type_from_stat(stat))
        }
        if hasattr(stat, 'st_birthtime'):
            details['created'] = stat.st_birthtime
        ctime_key = (
            'created'
            if _WINDOWS_PLATFORM
            else 'metadata_changed'
        )
        details[ctime_key] = stat.st_ctime
        return details

    @classmethod
    def _make_access_from_stat(cls, stat_result):
        access = {}
        access['permissions'] = Permissions(
            mode=stat_result.st_mode
        ).dump()
        access['gid'] = stat_result.st_gid
        access['uid'] = stat_result.st_uid
        try:
            access['group'] = grp.getgrgid(access['gid']).gr_name
        except KeyError:  # pragma: nocover
            pass

        try:
            access['user'] = pwd.getpwuid(access['uid']).pw_name
        except KeyError:  # pragma: nocover
            pass
        return access

    STAT_TO_RESOURCE_TYPE = {
        stat.S_IFDIR: ResourceType.directory,
        stat.S_IFCHR: ResourceType.character,
        stat.S_IFBLK: ResourceType.block_special_file,
        stat.S_IFREG: ResourceType.file,
        stat.S_IFIFO: ResourceType.fifo,
        stat.S_IFLNK: ResourceType.symlink,
        stat.S_IFSOCK: ResourceType.socket
    }

    @classmethod
    def _get_type_from_stat(cls, _stat):
        """Get the resource type from a stat_result object."""
        st_mode = _stat.st_mode
        st_type = stat.S_IFMT(st_mode)
        return cls.STAT_TO_RESOURCE_TYPE.get(st_type, ResourceType.unknown)

    # --------------------------------------------------------
    # Required Methods
    # --------------------------------------------------------

    def getinfo(self, path, namespaces=None):
        self._check()
        namespaces = namespaces or ()
        sys_path = self.getsyspath(path)
        with convert_os_errors('getinfo', path):
            _stat = os.stat(sys_path)

        info = {
            'basic': {
                'name': basename(path),
                'is_dir': stat.S_ISDIR(_stat.st_mode)
            }
        }
        if 'details' in namespaces:
            info['details'] = self._make_details_from_stat(_stat)
        if 'stat' in namespaces:
            info['stat'] = {
                k: getattr(stat, k)
                for k in dir(stat) if k.startswith('st_')
            }
        if 'access' in namespaces:
            info['access'] = self._make_access_from_stat(_stat)

        return Info(info)

    def listdir(self, path):
        self._check()
        sys_path = self._to_sys_path(path)
        with convert_os_errors('listdir', path, directory=True):
            names = os.listdir(sys_path)
        return names

    def makedir(self, path, permissions=None, recreate=False):
        self._check()
        mode = Permissions.get_mode(permissions)
        self.validatepath(path)
        sys_path = self._to_sys_path(path)
        with convert_os_errors('makedir', path):
            try:
                os.mkdir(sys_path, mode)
            except OSError as e:
                if e.errno == errno.ENOENT:
                    raise errors.ResourceNotFound(path)
                elif e.errno == errno.EEXIST and recreate:
                    pass
                else:
                    raise
            return self.opendir(path)

    def openbin(self, path, mode="r", buffering=-1, **options):
        validate_openbin_mode(mode)
        self._check()
        self.validatepath(path)
        if 'b' not in mode:
            mode += 'b'
        sys_path = self._to_sys_path(path)
        with convert_os_errors('openbin', path):
            binary_file = io.open(
                sys_path,
                mode=mode,
                buffering=buffering,
                **options
            )
        return binary_file

    def remove(self, path):
        self._check()
        sys_path = self._to_sys_path(path)
        with convert_os_errors('remove', path):
            try:
                os.remove(sys_path)
            except OSError as e:
                if e.errno == errno.EACCES and sys.platform == "win32":
                    # sometimes windows says this for attempts to remove a dir
                    if os.path.isdir(sys_path):  # pragma: nocover
                        raise errors.FileExpected(path)
                if e.errno == errno.EPERM and sys.platform == "darwin":
                    # sometimes OSX says this for attempts to remove a dir
                    if os.path.isdir(sys_path):  # pragma: nocover
                        raise errors.FileExpected(path)
                raise

    def removedir(self, path):
        self._check()
        _path = abspath(normpath(path))
        if _path == '/':
            raise errors.RemoveRootError()
        sys_path = self._to_sys_path(path)
        with convert_os_errors('removedir', path, directory=True):
            os.rmdir(sys_path)

    # --------------------------------------------------------
    # Optional Methods
    # --------------------------------------------------------

    def getsyspath(self, path):
        sys_path = self._to_sys_path(path)
        return sys_path

    def gettype(self, path):
        self._check()
        sys_path = self._to_sys_path(path)
        with convert_os_errors('gettype', path):
            stat = os.stat(sys_path)
        resource_type = self._get_type_from_stat(stat)
        return resource_type

    def hassyspath(self, path):
        return True

    def open(self,
             path,
             mode="r",
             buffering=-1,
             encoding=None,
             errors=None,
             newline=None,
             line_buffering=False,
             **options):
        validate_open_mode(mode)
        self._check()
        self.validatepath(path)
        sys_path = self._to_sys_path(path)
        with convert_os_errors('open', path):
            return io.open(
               sys_path,
               mode=mode,
               buffering=buffering,
               encoding=encoding,
               errors=errors,
               newline=newline,
               **options
            )

    def setinfo(self, path, info):
        self._check()
        sys_path = self._to_sys_path(path)
        if not os.path.exists(sys_path):
            raise errors.ResourceNotFound(path)
        if 'details' in info:
            details = info['details']
            if 'accessed' in details or 'modified' in details:
                accessed = details.get("accessed")
                modified = details.get("modified", accessed)
                accessed = int(modified if accessed is None else accessed)
                modified = int(modified)
                if accessed is not None or modified is not None:
                    with convert_os_errors('setinfo', path):
                        os.utime(sys_path, (accessed, modified))

    def scandir(self, path, namespaces=None):
        self._check()
        namespaces = namespaces or ()
        _path = abspath(normpath(path))
        sys_path = self._to_sys_path(_path)
        with convert_os_errors('scandir', path, directory=True):
            for dir_entry in scandir(sys_path):
                info = {
                    "basic": {
                        "name": dir_entry.name,
                        "is_dir": dir_entry.is_dir()
                    }
                }
                if 'details' in namespaces:
                    stat_result = dir_entry.stat()
                    info['details'] = \
                        self._make_details_from_stat(stat_result)
                if 'stat' in namespaces:
                    stat_result = dir_entry.stat()
                    info['stat'] = {
                        k: getattr(stat, k)
                        for k in dir(stat) if k.startswith('st_')
                    }
                if 'access' in namespaces:
                    stat_result = dir_entry.stat()
                    info['access'] =\
                        self._make_access_from_stat(stat_result)

                yield Info(info)
