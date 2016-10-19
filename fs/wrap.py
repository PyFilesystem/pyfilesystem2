from __future__ import print_function
from __future__ import unicode_literals

from .wrapfs import WrapFS
from .path import abspath, normpath, split
from .errors import ResourceReadOnly, ResourceNotFound
from .info import Info
from mode import check_writable


def read_only(fs):
    """
    Make a read-only filesystem.

    :param fs: A filesystem object.
    :returns: A read only version of ``fs``.

    """
    return WrapReadOnly(fs)


def cache_directory(fs):
    """
    Make a filesystem that caches directory information.

    :param fs: A filesystem object.
    :returns: A filesystem that caches results of ``scandir``, ``isdir``
        and other methods which read directory information.

    """
    return WrapCachedDir(fs)


class WrapCachedDir(WrapFS):
    """
    Caches filesystem directory information.

    This filesystem caches directory information retrieved from a
    scandir call. This *may* speed up code that calls ``isdir``,
    ``isfile``, or ``gettype`` too frequently.

    .. note::
        Using this wrap will prevent changes to directory information
        being visible to the filesystem object. Consequently it is best
        used only in a fairly limited scope where you don't expected
        anything on the filesystem to change.

    """

    wrap_name = 'cached-dir'

    def __init__(self, wrap_fs):
        super(WrapCachedDir, self).__init__(wrap_fs)
        self._cache = {}

    def scandir(self, path, namespaces=None):
        _path = abspath(normpath(path))
        cache_key = (_path, frozenset(namespaces or ()))
        if cache_key not in self._cache:
            _scan_result = self._wrap_fs.scandir(path, namespaces=namespaces)
            _dir = {info.name: info for info in _scan_result}
            self._cache[cache_key] = _dir
        gen_scandir = iter(self._cache[cache_key].values())
        return gen_scandir

    def getinfo(self, path, *namespaces):

        _path = abspath(normpath(path))
        if _path == '/':
            return Info({
                "basic": {
                    "name": "",
                    "is_dir": True
                }
            })
        dir_path, resource_name = split(_path)
        cache_key = (dir_path, frozenset(namespaces or ()))

        if cache_key not in self._cache:
            self.scandir(dir_path, namespaces=namespaces)

        _dir = self._cache[cache_key]
        try:
            info = _dir[resource_name]
        except KeyError:
            raise ResourceNotFound(path)
        return info

    # def gettype(self, path):
    #     resource_type = self.getinfo(path, 'details').type
    #     return resource_type

    def isdir(self, path):
        """Check a path exists and is a directory."""
        return self.getinfo(path).is_dir

    def isfile(self, path):
        """Check a path exists and is a file."""
        return not self.getinfo(path).is_dir


class WrapReadOnly(WrapFS):

    wrap_name = 'read-only'

    def makedir(self, path, permissions=None, recreate=False):
        self._check()
        raise ResourceReadOnly(path)

    def move(self, src_path, dst_path, overwrite=False):
        self._check()
        raise ResourceReadOnly(dst_path)

    def openbin(self, path, mode='r', buffering=-1, **options):
        self._check()
        if check_writable(mode):
            raise ResourceReadOnly(path)
        return self._wrap_fs.openbin(
            path,
            mode=mode,
            buffering=-1,
            **options
        )

    def remove(self, path):
        self._check()
        raise ResourceReadOnly(path)

    def removedir(self, path):
        self._check()
        raise ResourceReadOnly(path)

    def setinfo(self, path, info):
        self._check()
        raise ResourceReadOnly(path)

    def settext(self,
                path,
                contents,
                encoding='utf-8',
                errors=None,
                newline=None):
        self._check()
        raise ResourceReadOnly(path)

    def settimes(self, path, accessed=None, modified=None):
        self._check()
        raise ResourceReadOnly(path)

    def copy(self, src_path, dst_path):
        self._check()
        raise ResourceReadOnly(dst_path)

    def create(self, path, wipe=False):
        self._check()
        raise ResourceReadOnly(path)

    def makedirs(self, path, recreate=False, mode=0o777):
        self._check()
        raise ResourceReadOnly(path)

    def open(self,
             path,
             mode='r',
             buffering=-1,
             encoding=None,
             errors=None,
             newline=None,
             line_buffering=False,
             **options):
        self._check()
        if check_writable(mode):
            raise ResourceReadOnly(path)
        return self._wrap_fs.open(
            path,
            mode=mode,
            buffering=buffering,
            encoding=encoding,
            errors=errors,
            newline=newline,
            line_buffering=line_buffering,
            **options
        )

    def setbytes(self, path, contents):
        self._check()
        raise ResourceReadOnly(path)

    def setfile(self,
                path,
                file,
                encoding=None,
                errors=None,
                newline=None):
        self._check()
        raise ResourceReadOnly(path)

    def touch(self, path):
        self._check()
        raise ResourceReadOnly(path)

if __name__ == "__main__":
    from fs.opener import open_fs

    mem_fs = open_fs('mem://')
    mem_fs.makedir('foo')
    mem_fs = cache_directory(read_only(mem_fs))
    print(mem_fs)
    print(repr(mem_fs))
    sub_fs = mem_fs.opendir('foo')
    print(sub_fs)
    print(repr(sub_fs))
