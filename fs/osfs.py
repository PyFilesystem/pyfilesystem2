"""Manage the filesystem provided by your OS.

In essence, an `OSFS` is a thin layer over the `io` and `os` modules
of the Python standard library.
"""

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

ps = platform.system()
_WINDOWS_PLATFORM = ps == 'Windows'
_MAC_PLATFORM = ps == 'Darwin'
_NIX_PLATFORM = ps != _WINDOWS_PLATFORM and ps != _MAC_PLATFORM
del ps
_NIX_PY2 = _NIX_PLATFORM and six.PY2


@six.python_2_unicode_compatible
class OSFS(FS):
    """Create an OSFS.

    Arguments:
        root_path (str or ~os.PathLike): An OS path or path-like object to
            the location on your HD you wish to manage.
        create (bool, optional): Set to `True` to create the root directory
            if it does not already exist, otherwise the directory should exist
            prior to creating the ``OSFS`` instance (default `False`).
        create_mode (int, optional): The permissions that will be used to
            create the directory if ``create`` is `True` and the path doesn't
            exist, defaults to ``0o777``.

    Raises:
        `fs.errors.CreateFailed`: If ``root_path`` does not
            exist, or could not be created.

    Examples:
        >>> current_directory_fs = OSFS('.')
        >>> home_fs = OSFS('~/')
        >>> windows_system32_fs = OSFS('c://system32')

    """

    def __init__(self,
                 root_path,
                 create=False,
                 create_mode=0o777):
        """Create an OSFS instance.
        """
        super(OSFS, self).__init__()
        _root_path_native = fsencode(fspath(root_path))
        _root_path_native = os.path.expandvars(_root_path_native)
        _root_path_native = os.path.expanduser(_root_path_native)
        _root_path_native = os.path.abspath(_root_path_native)
        _root_path_native = os.path.normpath(_root_path_native)

        self.root_path_native = _root_path_native
        self.root_path = fsdecode(_root_path_native)

        if create:
            try:
                if not os.path.isdir(_root_path_native):
                    os.makedirs(_root_path_native, mode=create_mode)
            except OSError as error:
                raise errors.CreateFailed(
                    'unable to create {} ({})'.format(root_path, error)
                )
        else:
            if not os.path.isdir(_root_path_native):
                raise errors.CreateFailed(
                    'root path does not exist or is file'
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
            _meta["invalid_path_chars"] = \
                ''.join(six.unichr(n) for n in range(31)) + '\\:*?"<>|'
        else:
            _meta["invalid_path_chars"] = '\0'

            if 'PC_PATH_MAX' in os.pathconf_names:
                _meta['max_sys_path_length'] = (
                    os.pathconf(
                        _root_path_native,
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

    def _to_sys_path(self, path, as_bytes=False):
        """Convert a FS path to a path on the OS.
        If `as_bytes` is True, return fsencoded-bytes instead of Unicode.
        """
        root_path = self.root_path
        _path = path
        sep = '/'
        os_sep = os.sep

        if _NIX_PY2:
            root_path = self.root_path_native
            _path = fsencode(path)
            sep = b'/'
            os_sep = fsencode(os_sep)

        sys_path = os.path.join(
            root_path,
            _path.lstrip(sep).replace(sep, os_sep)
        )

        sys_path = fsdecode(sys_path)

        if as_bytes:
            return fsencode(sys_path)

        return sys_path

    @classmethod
    def _make_details_from_stat(cls, stat_result):
        """Make a *details* info dict from an `os.stat_result` object.
        """
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
        """Make an *access* info dict from an `os.stat_result` object.
        """
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
        """Get the resource type from an `os.stat_result` object.
        """
        st_mode = _stat.st_mode
        st_type = stat.S_IFMT(st_mode)
        return cls.STAT_TO_RESOURCE_TYPE.get(st_type, ResourceType.unknown)

    # --------------------------------------------------------
    # Required Methods
    # --------------------------------------------------------

    def _gettarget(self, sys_path):
        _sys_path = sys_path
        if _NIX_PY2:
            _sys_path = fsencode(_sys_path)
        try:
            target = os.readlink(_sys_path)
        except OSError:
            return None
        else:
            if _NIX_PY2 and target:
                target = fsdecode(target)
            return target

    def _make_link_info(self, sys_path):
        _target = self._gettarget(sys_path)
        link = {
            'target': fsdecode(_target) if _target else _target,
        }
        return link

    def _get_validated_syspath(self, path):
        """Return a validated, normalized and eventually encoded string or byte
           path.
        """
        _path = fsdecode(path) if path else path
        _path = self.validatepath(_path)
        return self._to_sys_path(_path, as_bytes=_NIX_PY2)

    def getinfo(self, path, namespaces=None):
        self.check()
        namespaces = namespaces or ()
        sys_path = self._get_validated_syspath(path)
        _lstat = None
        with convert_os_errors('getinfo', path):
            _stat = os.stat(sys_path)
            if 'lstat' in namespaces:
                _stat = os.lstat(sys_path)

        info = {
            'basic': {
                'name': fsdecode(basename(sys_path)),
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
        if 'lstat' in namespaces:
            info['lstat'] = {
                k: getattr(_lstat, k)
                for k in dir(_lstat) if k.startswith('st_')
            }
        if 'link' in namespaces:
            info['link'] = self._make_link_info(sys_path)
        if 'access' in namespaces:
            info['access'] = self._make_access_from_stat(_stat)

        return Info(info)

    def listdir(self, path):
        self.check()
        sys_path = self._get_validated_syspath(path)
        with convert_os_errors('listdir', path, directory=True):
            names = [fsdecode(f) for f in os.listdir(sys_path)]
        return names

    def makedir(self, path, permissions=None, recreate=False):
        self.check()
        mode = Permissions.get_mode(permissions)
        _path = fsdecode(path) if path else path
        _path = self.validatepath(_path)
        sys_path = self._get_validated_syspath(_path)
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
        _path = fsdecode(path) if path else path
        sys_path = self._get_validated_syspath(_path)
        with convert_os_errors('openbin', path):
            if six.PY2 and _mode.exclusive and self.exists(_path):
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
        sys_path = self._get_validated_syspath(path)
        with convert_os_errors('remove', path):
            try:
                os.remove(sys_path)
            except OSError as error:
                if error.errno == errno.EACCES and _WINDOWS_PLATFORM:
                    # sometimes windows says this for attempts to remove a dir
                    if os.path.isdir(sys_path):  # pragma: nocover
                        raise errors.FileExpected(path)
                if error.errno == errno.EPERM and _MAC_PLATFORM:
                    # sometimes OSX says this for attempts to remove a dir
                    if os.path.isdir(sys_path):  # pragma: nocover
                        raise errors.FileExpected(path)
                raise

    def removedir(self, path):
        self.check()
        _path = fsdecode(path) if path else path
        _path = self.validatepath(_path)
        if _path == '/':
            raise errors.RemoveRootError()

        sys_path = self._to_sys_path(_path, as_bytes=_NIX_PY2)
        with convert_os_errors('removedir', path, directory=True):
            os.rmdir(sys_path)

    # --------------------------------------------------------
    # Optional Methods
    # --------------------------------------------------------

    def getsyspath(self, path):
        _path = fsdecode(path) if path else path
        sys_path = self._to_sys_path(_path, as_bytes=False)
        return sys_path

    def geturl(self, path, purpose='download'):
        if purpose != 'download':
            raise NoURL(path, purpose)
        # FIXME: segments might need to be URL/percent-encoded instead
        return "file://" + self.getsyspath(path)

    def gettype(self, path):
        self.check()
        sys_path = self._get_validated_syspath(path)
        with convert_os_errors('gettype', path):
            stat = os.stat(sys_path)
        resource_type = self._get_type_from_stat(stat)
        return resource_type

    def islink(self, path):
        self.check()
        sys_path = self._get_validated_syspath(path)
        if not self.exists(path):
            raise errors.ResourceNotFound(path)
        with convert_os_errors('islink', path):
            return os.path.islink(sys_path)

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
        sys_path = self._get_validated_syspath(path)
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
        sys_path = self._get_validated_syspath(path)
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
            sys_path = self._get_validated_syspath(path)
            sys_path_u = fsdecode(sys_path)
            with convert_os_errors('scandir', path, directory=True):
                for dir_entry in scandir(sys_path):
                    entry_name = fsdecode(dir_entry.name)
                    info = {
                        "basic": {
                            "name": entry_name,
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
                    if 'lstat' in namespaces:
                        lstat_result = dir_entry.stat(follow_symlinks=False)
                        info['lstat'] = {
                            k: getattr(lstat_result, k)
                            for k in dir(lstat_result) if k.startswith('st_')
                        }
                    if 'link' in namespaces:
                        entry_path = os.path.join(sys_path_u, entry_name)
                        info['link'] = self._make_link_info(entry_path)
                    if 'access' in namespaces:
                        stat_result = dir_entry.stat()
                        info['access'] = \
                            self._make_access_from_stat(stat_result)

                    yield Info(info)

    else:

        def _scandir(self, path, namespaces=None):
            self.check()
            namespaces = namespaces or ()
            sys_path = self._get_validated_syspath(path)
            sys_path_u = fsdecode(sys_path)
            with convert_os_errors('scandir', path, directory=True):
                for entry_name in os.listdir(sys_path):
                    entry_name = fsdecode(entry_name)
                    entry_path = os.path.join(sys_path_u, entry_name)
                    entry_path_b = fsdecode(entry_path)
                    stat_result = os.stat(entry_path_b)

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
                    if 'lstat' in namespaces:
                        lstat_result = os.lstat(entry_path_b)
                        info['lstat'] = {
                            k: getattr(lstat_result, k)
                            for k in dir(lstat_result) if k.startswith('st_')
                        }
                    if 'link' in namespaces:
                        info['link'] = self._make_link_info(entry_path)
                    if 'access' in namespaces:
                        info['access'] = \
                            self._make_access_from_stat(stat_result)

                    yield Info(info)


    def scandir(self, path, namespaces=None, page=None):
        path = fsdecode(path) if path else path
        iter_info = self._scandir(path, namespaces=namespaces)
        if page is not None:
            start, end = page
            iter_info = itertools.islice(iter_info, start, end)
        return iter_info
