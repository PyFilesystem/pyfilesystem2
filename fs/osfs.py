from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import errno
import io
import itertools
import logging
import os
import platform
import stat
import sys

import six

try:
    from os import scandir
except ImportError:
    try:
        from scandir import scandir
    except ImportError:  # pragma: nocover
        scandir = None

from . import errors
from .errors import FileExists
from .base import FS
from .enums import ResourceType
from ._fscompat import fsencode, fsdecode, fspath
from .info import Info
from .path import basename
from .permissions import Permissions
from .error_tools import convert_os_errors
from .mode import Mode, validate_open_mode
from .errors import NoURL

log = logging.getLogger('fs.osfs')


_WINDOWS_PLATFORM = platform.system() == 'Windows'


@six.python_2_unicode_compatible
class OSFS(FS):
    """
    Create an OSFS.

    :param root_path: An OS path or path-like object to the location on
        your HD you wish to manage.
    :type root_path: str or path-like
    :param create: Set to ``True`` to create the root directory if it
        does not already exist, otherwise the directory should exist
        prior to creating the ``OSFS`` instance.
    :type create: bool
    :param int create_mode: The permissions that will be used to create
        the directory if ``create`` is True and the path doesn't exist,
        defaults to ``0o777``.
    :raises `fs.errors.CreateFailed`: If ``root_path`` does not
        exists, or could not be created.


    Here are some examples of creating ``OSFS`` objects::

        current_directory_fs = OSFS('.')
        home_fs = OSFS('~/')
        windows_system32_fs = OSFS('c://system32')

    """

    def __init__(self,
                 root_path,
                 create=False,
                 create_mode=0o777):
        """Create an OSFS instance."""

        super(OSFS, self).__init__()
        root_path = fsdecode(fspath(root_path))
        _root_path = os.path.expanduser(os.path.expandvars(root_path))
        _root_path = os.path.normpath(os.path.abspath(_root_path))
        self.root_path = _root_path

        if create:
            try:
                if not os.path.isdir(_root_path):
                    os.makedirs(_root_path, mode=create_mode)
            except OSError as error:
                raise errors.CreateFailed(
                    'unable to create {} ({})'.format(root_path, error)
                )
        else:
            if not os.path.isdir(_root_path):
                raise errors.CreateFailed(
                    'root path does not exists'
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
                ''.join(six.unichr(n) for n in range(31)) + '\\:*?"<>|'
        else:
            _meta["invalid_path_chars"] = '\0'

            if 'PC_PATH_MAX' in os.pathconf_names:
                _meta['max_sys_path_length'] = (
                    os.pathconf(
                        fsencode(_root_path),
                        os.pathconf_names['PC_PATH_MAX']
                    )
                )

    def __repr__(self):
        _fmt = "{}({!r})"
        return _fmt.format(self.__class__.__name__,
                           self.root_path)

    def __str__(self):
        fmt = "<{} '{}'>"
        return fmt.format(self.__class__.__name__.lower(),
                          self.root_path)

    def _to_sys_path(self, path):
        """Convert a FS path to a path on the OS."""
        sys_path = os.path.join(
            self.root_path,
            path.lstrip('/').replace('/', os.sep)
        )
        return sys_path

    @classmethod
    def _make_details_from_stat(cls, stat_result):
        """Make an info dict from a stat_result object."""
        details = {
            '_write': ['accessed', 'modified'],
            'accessed': stat_result.st_atime,
            'modified': stat_result.st_mtime,
            'size': stat_result.st_size,
            'type': int(cls._get_type_from_stat(stat_result))
        }
        # On other Unix systems (such as FreeBSD), the following
        # attributes may be available (but may be only filled out if
        # root tries to use them):
        details['created'] = getattr(stat_result, 'st_birthtime', None)
        ctime_key = (
            'created'
            if _WINDOWS_PLATFORM
            else 'metadata_changed'
        )
        details[ctime_key] = stat_result.st_ctime
        return details

    @classmethod
    def _make_access_from_stat(cls, stat_result):
        access = {}
        access['permissions'] = Permissions(
            mode=stat_result.st_mode
        ).dump()
        access['gid'] = stat_result.st_gid
        access['uid'] = stat_result.st_uid
        if not _WINDOWS_PLATFORM:
            import grp
            import pwd
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
        self.check()
        namespaces = namespaces or ()
        _path = self.validatepath(path)
        sys_path = self.getsyspath(_path)
        with convert_os_errors('getinfo', path):
            _stat = os.stat(sys_path)

        info = {
            'basic': {
                'name': basename(_path),
                'is_dir': stat.S_ISDIR(_stat.st_mode)
            }
        }
        if 'details' in namespaces:
            info['details'] = self._make_details_from_stat(_stat)
        if 'stat' in namespaces:
            info['stat'] = {
                k: getattr(_stat, k)
                for k in dir(_stat) if k.startswith('st_')
            }
        if 'access' in namespaces:
            info['access'] = self._make_access_from_stat(_stat)

        return Info(info)

    def listdir(self, path):
        self.check()
        _path = self.validatepath(path)
        sys_path = self._to_sys_path(_path)
        with convert_os_errors('listdir', path, directory=True):
            names = os.listdir(sys_path)
        return names

    def makedir(self, path, permissions=None, recreate=False):
        self.check()
        mode = Permissions.get_mode(permissions)
        _path = self.validatepath(path)
        sys_path = self._to_sys_path(_path)
        with convert_os_errors('makedir', path, directory=True):
            try:
                os.mkdir(sys_path, mode)
            except OSError as error:
                if error.errno == errno.ENOENT:
                    raise errors.ResourceNotFound(path)
                elif error.errno == errno.EEXIST and recreate:
                    pass
                else:
                    raise
            return self.opendir(_path)

    def openbin(self, path, mode="r", buffering=-1, **options):
        _mode = Mode(mode)
        _mode.validate_bin()
        self.check()
        _path = self.validatepath(path)
        sys_path = self._to_sys_path(_path)
        with convert_os_errors('openbin', path):
            if six.PY2 and _mode.exclusive and self.exists(path):
                raise errors.FileExists(path)
            binary_file = io.open(
                sys_path,
                mode=_mode.to_platform_bin(),
                buffering=buffering,
                **options
            )
        return binary_file

    def remove(self, path):
        self.check()
        _path = self.validatepath(path)
        sys_path = self._to_sys_path(_path)
        with convert_os_errors('remove', path):
            try:
                os.remove(sys_path)
            except OSError as error:
                if error.errno == errno.EACCES and sys.platform == "win32":
                    # sometimes windows says this for attempts to remove a dir
                    if os.path.isdir(sys_path):  # pragma: nocover
                        raise errors.FileExpected(path)
                if error.errno == errno.EPERM and sys.platform == "darwin":
                    # sometimes OSX says this for attempts to remove a dir
                    if os.path.isdir(sys_path):  # pragma: nocover
                        raise errors.FileExpected(path)
                raise

    def removedir(self, path):
        self.check()
        _path = self.validatepath(path)
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

    def geturl(self, path, purpose='download'):
        if purpose != 'download':
            raise NoURL(path, purpose)
        return "file://" + self.getsyspath(path)

    def gettype(self, path):
        self.check()
        sys_path = self._to_sys_path(path)
        with convert_os_errors('gettype', path):
            stat = os.stat(sys_path)
        resource_type = self._get_type_from_stat(stat)
        return resource_type

    def open(self,
             path,
             mode="r",
             buffering=-1,
             encoding=None,
             errors=None,
             newline='',
             line_buffering=False,
             **options):
        _mode = Mode(mode)
        validate_open_mode(mode)
        self.check()
        _path = self.validatepath(path)
        sys_path = self._to_sys_path(_path)
        with convert_os_errors('open', path):
            if six.PY2 and _mode.exclusive and self.exists(path):
                raise FileExists(path)
            _encoding = encoding or 'utf-8'
            return io.open(
                sys_path,
                mode=_mode.to_platform(),
                buffering=buffering,
                encoding=None if _mode.binary else _encoding,
                errors=errors,
                newline=None if _mode.binary else newline,
                **options
            )

    def setinfo(self, path, info):
        self.check()
        _path = self.validatepath(path)
        sys_path = self._to_sys_path(_path)
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


    if scandir:
        def _scandir(self, path, namespaces=None):
            self.check()
            namespaces = namespaces or ()
            _path = self.validatepath(path)
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
                            k: getattr(stat_result, k)
                            for k in dir(stat_result) if k.startswith('st_')
                        }
                    if 'access' in namespaces:
                        stat_result = dir_entry.stat()
                        info['access'] =\
                            self._make_access_from_stat(stat_result)

                    yield Info(info)

    else:

        def _scandir(self, path, namespaces=None):
            self.check()
            namespaces = namespaces or ()
            _path = self.validatepath(path)
            sys_path = self._to_sys_path(_path)
            with convert_os_errors('scandir', path, directory=True):
                for entry_name in os.listdir(sys_path):
                    entry_path = os.path.join(sys_path, entry_name)
                    stat_result = os.stat(entry_path)
                    info = {
                        "basic": {
                            "name": entry_name,
                            "is_dir": stat.S_ISDIR(stat_result.st_mode),
                        }
                    }
                    if 'details' in namespaces:
                        info['details'] = \
                            self._make_details_from_stat(stat_result)
                    if 'stat' in namespaces:
                        info['stat'] = {
                            k: getattr(stat_result, k)
                            for k in dir(stat_result) if k.startswith('st_')
                        }
                    if 'access' in namespaces:
                        info['access'] =\
                            self._make_access_from_stat(stat_result)

                    yield Info(info)


    def scandir(self, path, namespaces=None, page=None):
        iter_info = self._scandir(path, namespaces=namespaces)
        if page is not None:
            start, end = page
            iter_info = itertools.islice(iter_info, start, end)
        return iter_info
