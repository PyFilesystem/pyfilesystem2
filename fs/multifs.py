from __future__ import absolute_import
from __future__ import unicode_literals
from __future__ import print_function

from collections import namedtuple
from operator import itemgetter

from .base import FS
from .mode import check_writable
from . import errors
from .path import abspath, normpath


_PrioritizedFS = namedtuple(
    '_PrioritizedFS',
    ['priority', 'fs']
)


class MultiFS(FS):
    """
    A filesystem that delegates to a sequence of other filesystems.

    Operations on the MultiFS will try each 'child' filesystem in order,
    until it succeeds. In effect, creating a filesystem that combines
    the files and dirs of its children.

    """

    _meta = {
        "virtual": True,
        "read_only": False,
        "case_insensitive": False
    }

    def __init__(self, auto_close=True):
        super(MultiFS, self).__init__()

        self._auto_close = auto_close
        self.write_fs = None

        self._write_fs_name = None
        self._sort_index = 0
        self._filesystems = {}
        self._fs_sequence = None
        self._closed = False

    def __repr__(self):
        if self._auto_close:
            return "MultiFS()"
        else:
            return "MultiFS(auto_close=False)"

    def __str__(self):
        return "<multifs>"

    def add_fs(self, name, fs, write=False, priority=0):
        """
        Adds a filesystem to the MultiFS.

        :param name: A unique name to refer to the filesystem being
            added.
        :type name: str
        :param fs: The filesystem to add
        :type fs: Filesystem
        :param write: If this value is True, then the ``fs`` will be
            used as the writeable FS.
        :type write: bool
        :param priority: An integer that denotes the priority of the
            filesystem being added. Filesystems will be searched in
            descending priority order and then by the reverse order they
            were added. So by default, the most recently added
            filesystem will be looked at first.
        :type priority: int

        """

        self._filesystems[name] = _PrioritizedFS(
            priority=(priority, self._sort_index),
            fs=fs
        )
        self._sort_index += 1
        self._resort()

        if write:
            self.write_fs = fs
            self._write_fs_name = name

    def get_fs(self, name):
        """
        Get a filesystem from its name.

        :param name: The name of a filesystem previously added.
        :type name: str

        """
        return self._filesystems[name].fs

    def _resort(self):
        """Force iterate_fs to re-sort on next reference."""
        self._fs_sequence = None

    def iterate_fs(self):
        """Get iterator that returns (name, fs) in priority order."""
        if self._fs_sequence is None:
            self._fs_sequence = [
                (name, fs)
                for name, (_order, fs) in
                sorted(
                    self._filesystems.items(),
                    key=itemgetter(1),
                    reverse=True
                )
            ]
        return iter(self._fs_sequence)

    def _delegate(self, path):
        """Get a filesystem which has a given path."""
        for _name, fs in self.iterate_fs():
            if fs.exists(path):
                return fs
        return None

    def _delegate_required(self, path):
        fs = self._delegate(path)
        if fs is None:
            raise errors.ResourceNotFound(path)
        return fs

    def _require_writable(self, path):
        if self.write_fs is None:
            raise errors.ResourceReadOnly(path)

    def which(self, path, mode="r"):
        """
        Get a tuple of (name, filesystem) that the given path would map
        to.

        :param path: A path on the filesystem.
        :type path: str
        :param mode: A open mode.
        :type mode: str

        """

        if check_writable(mode):
            return self._write_fs_name, self.write_fs
        for name, fs in self.iterate_fs():
            if fs.exists(path):
                return name, fs
        return None, None

    def close(self):
        self._closed = True
        if self._auto_close:
            try:
                for _order, fs in self._filesystems.values():
                    fs.close()
            finally:
                self._filesystems.clear()
                self._resort()

    def getinfo(self, path, namespaces=None):
        self.check()
        namespaces = namespaces or ()
        fs = self._delegate(path)
        if fs is None:
            raise errors.ResourceNotFound(path)
        _path = abspath(normpath(path))
        info = fs.getinfo(_path, namespaces=namespaces)
        return info

    def listdir(self, path):
        self.check()
        directory = []
        exists = False
        for _name, _fs in self.iterate_fs():
            try:
                directory.extend(_fs.listdir(path))
            except errors.ResourceNotFound:
                pass
            else:
                exists = True
        if not exists:
            raise errors.ResourceNotFound(path)
        return directory

    def makedir(self, path, permissions=None, recreate=False):
        self.check()
        self._require_writable(path)
        return self.write_fs.makedir(
            path, permissions=permissions, recreate=recreate)

    def openbin(self, path, mode='r', buffering=-1, **options):
        self.check()
        if check_writable(mode):
            self._require_writable(path)
            _fs = self.write_fs
        else:
            _fs = self._delegate_required(path)
        return _fs.openbin(
            path,
            mode=mode,
            buffering=buffering,
            **options
        )

    def remove(self, path):
        self.check()
        fs = self._delegate_required(path)
        return fs.remove(path)

    def removedir(self, path):
        self.check()
        fs = self._delegate_required(path)
        return fs.removedir(path)

    def scandir(self, path, namespaces=None, page=None):
        self.check()
        seen = set()
        exists = False
        for _name, fs in self.iterate_fs():
            try:
                for info in fs.scandir(path, namespaces=namespaces, page=page):
                    if info.name not in seen:
                        yield info
                        seen.add(info.name)
                exists = True
            except errors.ResourceNotFound:
                pass

        if not exists:
            raise errors.ResourceNotFound(path)

    def getbytes(self, path):
        self.check()
        fs = self._delegate(path)
        if fs is None:
            raise errors.ResourceNotFound(path)
        return fs.getbytes(path)

    def gettext(self, path, encoding=None, errors=None, newline=''):
        self.check()
        fs = self._delegate_required(path)
        return fs.gettext(
            path,
            encoding=encoding,
            errors=errors,
            newline=newline
        )

    def getsize(self, path):
        self.check()
        fs = self._delegate_required(path)
        return fs.getsize(path)

    def getsyspath(self, path):
        self.check()
        fs = self._delegate_required(path)
        return fs.getsyspath(path)

    def gettype(self, path):
        self.check()
        fs = self._delegate_required(path)
        return fs.gettype(path)

    def geturl(self, path, purpose='download'):
        self.check()
        fs = self._delegate_required(path)
        return fs.geturl(path, purpose=purpose)

    def hassyspath(self, path):
        self.check()
        fs = self._delegate_required(path)
        return fs.hassyspath(path)

    def hasurl(self, path, purpose='download'):
        self.check()
        fs = self._delegate_required(path)
        return fs.hasurl(path, purpose=purpose)

    def isdir(self, path):
        self.check()
        fs = self._delegate(path)
        return fs and fs.isdir(path)

    def isfile(self, path):
        self.check()
        fs = self._delegate(path)
        return fs and fs.isfile(path)

    def setinfo(self, path, info):
        self.check()
        self._require_writable(path)
        return self.write_fs.setinfo(path, info)

    def validatepath(self, path):
        self.check()
        if self.write_fs is not None:
            self.write_fs.validatepath(path)
        else:
            super(MultiFS, self).validatepath(path)

    def makedirs(self, path, permissions=None, recreate=False):
        self.check()
        self._require_writable(path)
        return self.write_fs.makedirs(
            path,
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
             **kwargs):
        self.check()
        if check_writable(mode):
            self._require_writable(path)
            _fs = self.write_fs
        else:
            _fs = self._delegate_required(path)
        return _fs.open(
            path,
            mode=mode,
            buffering=buffering,
            encoding=encoding,
            errors=errors,
            newline=newline,
            **kwargs
        )

    def setbinfile(self, path, file):
        self._require_writable(path)
        self.write_fs.setbinfile(path, file)

    def setbytes(self, path, contents):
        self._require_writable(path)
        return self.write_fs.setbytes(path, contents)

    def settext(self,
                path,
                contents,
                encoding='utf-8',
                errors=None,
                newline=''):
        self._require_writable(path)
        return self.write_fs.settext(
            path,
            contents,
            encoding=encoding,
            errors=errors,
            newline=newline
        )
