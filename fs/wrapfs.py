from __future__ import unicode_literals

import six

from . import errors
from .base import FS
from .copy import copy_file
from .info import Info
from .move import move_file
from .path import abspath, normpath
from .error_tools import unwrap_errors


@six.python_2_unicode_compatible
class WrapFS(FS):
    """"
    A proxy for a filesystem object.

    This class exposes an filesystem interface, where the data is
    stored on another filesystem(s), and is the basis for
    :class:`~fs.subfs.SubFS` and other *virtual* filesystems.

    """

    wrap_name = None

    def __init__(self, wrap_fs):
        self._wrap_fs = wrap_fs
        super(WrapFS, self).__init__()

    def __repr__(self):
        return "{}({!r})".format(
            self.__class__.__name__,
            self._wrap_fs
        )

    def __str__(self):
        wraps = []
        _fs = self
        while hasattr(_fs, '_wrap_fs'):
            wrap_name = getattr(_fs, 'wrap_name', None)
            if wrap_name is not None:
                wraps.append(wrap_name)
            _fs = _fs._wrap_fs
        if wraps:
            _str = "{}({})".format(_fs, ', '.join(wraps[::-1]))
        else:
            _str = "{}".format(_fs)
        return _str

    def delegate_path(self, path):
        """
        Encode a path for proxied filesystem.

        :param path: A path on the fileystem.
        :type path: str
        :returns: a tuple of <filesystem>, <new path>
        :rtype: tuple

        """
        return self._wrap_fs, path

    def delegate_fs(self):
        """
        Get the filesystem.

        This method should return a filesystem for methods not
        associated with a path, e.g. :meth:`~fs.base.FS.getmeta`.

        """
        return self._wrap_fs


    def appendbytes(self, path, data):
        self.check()
        _fs, _path = self.delegate_path(path)
        with unwrap_errors(path):
            return _fs.appendbytes(_path, data)

    def appendtext(self, path, text,
                   encoding='utf-8', errors=None, newline=''):
        self.check()
        _fs, _path = self.delegate_path(path)
        with unwrap_errors(path):
            return _fs.appendtext(_path,
                                  text,
                                  encoding=encoding,
                                  errors=errors,
                                  newline=newline)

    def getinfo(self, path, namespaces=None):
        self.check()
        _fs, _path = self.delegate_path(path)
        with unwrap_errors(path):
            raw_info = _fs.getinfo(_path, namespaces=namespaces).raw
        if abspath(normpath(path)) == '/':
            raw_info = raw_info.copy()
            raw_info['basic']['name'] = ''
        info = Info(raw_info)
        return info

    def listdir(self, path):
        self.check()
        _fs, _path = self.delegate_path(path)
        with unwrap_errors(path):
            dir_list = _fs.listdir(_path)
        return dir_list

    def lock(self):
        self.check()
        _fs = self.delegate_fs()
        return _fs.lock()

    def makedir(self, path, permissions=None, recreate=False):
        self.check()
        _fs, _path = self.delegate_path(path)
        with unwrap_errors(path):
            return _fs.makedir(
                _path,
                permissions=permissions,
                recreate=recreate
            )

    def move(self, src_path, dst_path, overwrite=False):
        # A custom move permits a potentially optimized code path
        src_fs, _src_path = self.delegate_path(src_path)
        dst_fs, _dst_path = self.delegate_path(dst_path)
        with unwrap_errors({_src_path: src_path, _dst_path: dst_path}):
            if not overwrite and dst_fs.exists(_dst_path):
                raise errors.DestinationExists(_dst_path)
            move_file(src_fs, _src_path, dst_fs, _dst_path)

    def openbin(self, path, mode='r', buffering=-1, **options):
        self.check()
        _fs, _path = self.delegate_path(path)
        with unwrap_errors(path):
            bin_file = _fs.openbin(
                _path,
                mode=mode,
                buffering=-1,
                **options
            )
        return bin_file

    def remove(self, path):
        self.check()
        _fs, _path = self.delegate_path(path)
        with unwrap_errors(path):
            _fs.remove(_path)

    def removedir(self, path):
        self.check()
        _path = abspath(normpath(path))
        if _path == '/':
            raise errors.RemoveRootError()
        _fs, _path = self.delegate_path(path)
        with unwrap_errors(path):
            _fs.removedir(_path)

    def scandir(self, path, namespaces=None, page=None):
        self.check()
        _fs, _path = self.delegate_path(path)
        with unwrap_errors(path):
            for info in _fs.scandir(_path,
                                    namespaces=namespaces,
                                    page=page):
                yield info

    def setinfo(self, path, info):
        self.check()
        _fs, _path = self.delegate_path(path)
        return _fs.setinfo(_path, info)

    def settimes(self, path, accessed=None, modified=None):
        self.check()
        _fs, _path = self.delegate_path(path)
        with unwrap_errors(path):
            _fs.settimes(_path, accessed=accessed, modified=modified)

    def touch(self, path):
        self.check()
        _fs, _path = self.delegate_path(path)
        with unwrap_errors(path):
            _fs.touch(_path)

    def copy(self, src_path, dst_path, overwrite=False):
        src_fs, _src_path = self.delegate_path(src_path)
        dst_fs, _dst_path = self.delegate_path(dst_path)
        with unwrap_errors({_src_path: src_path, _dst_path: dst_path}):
            if not overwrite and dst_fs.exists(_dst_path):
                raise errors.DestinationExists(_dst_path)
            copy_file(src_fs, _src_path, dst_fs, _dst_path)

    def create(self, path, wipe=False):
        self.check()
        _fs, _path = self.delegate_path(path)
        with unwrap_errors(path):
            _fs.create(_path, wipe=wipe)

    def desc(self, path):
        self.check()
        _fs, _path = self.delegate_path(path)
        with unwrap_errors(path):
            desc = _fs.desc(_path)
        return desc

    def exists(self, path):
        self.check()
        _fs, _path = self.delegate_path(path)
        with unwrap_errors(path):
            exists = _fs.exists(_path)
        return exists

    def filterdir(self,
                  path,
                  exclude_dirs=False,
                  exclude_files=False,
                  files=None,
                  dirs=None,
                  namespaces=None,
                  page=None):
        self.check()
        _fs, _path = self.delegate_path(path)
        iter_files = iter(_fs.filterdir(
            _path,
            exclude_dirs=exclude_dirs,
            exclude_files=exclude_files,
            files=files,
            dirs=dirs,
            namespaces=namespaces,
            page=page
        ))
        with unwrap_errors(path):
            for info in iter_files:
                yield info

    def getbytes(self, path):
        self.check()
        _fs, _path = self.delegate_path(path)
        with unwrap_errors(path):
            _bytes = _fs.getbytes(_path)
        return _bytes

    def gettext(self, path, encoding=None, errors=None, newline=''):
        self.check()
        _fs, _path = self.delegate_path(path)
        with unwrap_errors(path):
            _text = _fs.gettext(_path,
                                encoding=encoding,
                                errors=errors,
                                newline=newline)
        return _text

    def getmeta(self, namespace='standard'):
        self.check()
        meta = self.delegate_fs().getmeta(namespace=namespace)
        return meta

    def getsize(self, path):
        self.check()
        _fs, _path = self.delegate_path(path)
        with unwrap_errors(path):
            size = _fs.getsize(_path)
        return size

    def getsyspath(self, path):
        self.check()
        _fs, _path = self.delegate_path(path)
        with unwrap_errors(path):
            sys_path = _fs.getsyspath(_path)
        return sys_path

    def gettype(self, path):
        self.check()
        _fs, _path = self.delegate_path(path)
        with unwrap_errors(path):
            _type = _fs.gettype(_path)
        return _type

    def geturl(self, path, purpose='download'):
        self.check()
        _fs, _path = self.delegate_path(path)
        with unwrap_errors(path):
            return _fs.geturl(_path, purpose=purpose)

    def hassyspath(self, path):
        self.check()
        _fs, _path = self.delegate_path(path)
        with unwrap_errors(path):
            has_sys_path = _fs.hassyspath(_path)
        return has_sys_path

    def hasurl(self, path, purpose='download'):
        self.check()
        _fs, _path = self.delegate_path(path)
        with unwrap_errors(path):
            has_url = _fs.hasurl(_path, purpose=purpose)
        return has_url

    def isdir(self, path):
        self.check()
        _fs, _path = self.delegate_path(path)
        with unwrap_errors(path):
            _isdir = _fs.isdir(_path)
        return _isdir

    def isfile(self, path):
        self.check()
        _fs, _path = self.delegate_path(path)
        with unwrap_errors(path):
            _isfile = _fs.isfile(_path)
        return _isfile

    def makedirs(self, path, permissions=None, recreate=False):
        self.check()
        _fs, _path = self.delegate_path(path)
        return _fs.makedirs(
            _path,
            permissions=permissions,
            recreate=recreate
        )

    def open(self,
             path,
             mode='r',
             buffering=-1,
             encoding=None,
             errors=None,
             newline='',
             line_buffering=False,
             **options):
        self.check()
        _fs, _path = self.delegate_path(path)
        with unwrap_errors(path):
            open_file = _fs.open(
                _path,
                mode=mode,
                buffering=buffering,
                encoding=encoding,
                errors=errors,
                newline=newline,
                line_buffering=line_buffering,
                **options
            )
        return open_file

    def opendir(self, path):
        from .subfs import SubFS
        if not self.getinfo(path).is_dir:
            raise errors.DirectoryExpected(
                path=path
            )
        with unwrap_errors(path):
            return SubFS(self, path)

    def setbytes(self, path, contents):
        self.check()
        _fs, _path = self.delegate_path(path)
        with unwrap_errors(path):
            _fs.setbytes(_path, contents)

    def setbinfile(self, path, file):
        self.check()
        _fs, _path = self.delegate_path(path)
        with unwrap_errors(path):
            _fs.setbinfile(_path, file)

    def setfile(self,
                path,
                file,
                encoding=None,
                errors=None,
                newline=''):
        self.check()
        _fs, _path = self.delegate_path(path)
        with unwrap_errors(path):
            _fs.setfile(
                _path,
                file,
                encoding=encoding,
                errors=errors,
                newline=newline
            )

    def validatepath(self, path):
        self.check()
        _fs, _path = self.delegate_path(path)
        with unwrap_errors(path):
            _fs.validatepath(_path)
