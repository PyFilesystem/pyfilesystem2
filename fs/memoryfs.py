
from __future__ import absolute_import
from __future__ import unicode_literals

import contextlib
import io
import os
import time

from collections import OrderedDict
from threading import RLock

import six

from . import errors
from .base import FS
from .enums import ResourceType
from .info import Info
from .path import abspath
from .path import iteratepath
from .path import normpath
from .path import split
from .mode import validate_openbin_mode


@six.python_2_unicode_compatible
class _MemoryFile(object):

    def __init__(self, path, memory_fs, bytes_io, mode, lock):
        self._path = path
        self._memory_fs = memory_fs
        self._bytes_io = bytes_io
        self._mode = mode
        self._lock = lock

        self.accessed_time = time.time()
        self.modified_time = time.time()
        self.closed = False
        self.pos = 0

        if 'a' in mode:
            with self._lock:
                self._bytes_io.seek(0, os.SEEK_END)
                self.pos = self._bytes_io.tell()
        elif 'w' in mode:
            with self._lock:
                self._bytes_io.seek(0)
                self._bytes_io.truncate()

    def __str__(self):
        _template = "<memoryfile '{path}' '{mode}'>"
        return _template.format(path=self._path, mode=self._mode)

    @contextlib.contextmanager
    def _seek_lock(self):
        with self._lock:
            self._bytes_io.seek(self.pos)
            yield
            self.pos = self._bytes_io.tell()

    def _on_modify(self):
        """Called when file data is modified."""
        self.modified_time = time.time()
        self._memory_fs._on_modify_file(
            self._path,
            self.modified_time
        )

    def _on_access(self):
        """Called when file is accessed."""
        self.accessed_time = time.time()
        self._memory_fs._on_access_file(
            self._path,
            self.accessed_time
        )

    # def fileno(self):
    #     raise io.UnsupportedOperation('fileno')

    def flush(self):
        pass

    def __iter__(self):
        self._bytes_io.seek(self.pos)
        for line in self._bytes_io:
            yield line

    def next(self):
        with self._seek_lock():
            return next(self._bytes_io)

    __next__ = next

    def readline(self, *args, **kwargs):
        with self._seek_lock():
            self._on_access()
            return self._bytes_io.readline(*args, **kwargs)

    def close(self):
        with self._lock:
            if not self.closed:
                self._memory_fs._on_close_file(self, self._path)
            self.closed = True

    def read(self, size=None):
        if size is None:
            size = -1
        with self._seek_lock():
            self._on_access()
            return self._bytes_io.read(size)

    def readlines(self):
        with self._seek_lock():
            return self._bytes_io.readlines()

    def seek(self, *args, **kwargs):
        with self._seek_lock():
            self._on_access()
            return self._bytes_io.seek(*args, **kwargs)

    def tell(self):
        return self.pos

    def truncate(self, *args, **kwargs):
        with self._seek_lock():
            self._on_modify()
            self._bytes_io.truncate(*args, **kwargs)

    def write(self, data):
        with self._seek_lock():
            self._on_modify()
            self._bytes_io.write(data)

    def writelines(self, sequence):
        with self._seek_lock():
            self._on_modify()
            self._bytes_io.writelines(sequence)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()


class _DirEntry(object):

    def __init__(self, resource_type, name):
        self.resource_type = resource_type
        self.name = name
        self._dir = OrderedDict()
        self._open_files = []
        self._bytes_file = None
        self._lock = RLock()

        _t = time.time()
        self.created_time = _t
        self.accessed_time = _t
        self.modified_time = _t

        if not self.is_dir:
            self._bytes_file = io.BytesIO()

    @property
    def bytes_file(self):
        return self._bytes_file

    @property
    def is_dir(self):
        return self.resource_type == ResourceType.directory

    @property
    def size(self):
        with self._lock:
            if self.is_dir:
                return 0
            else:
                self._bytes_file.seek(0, os.SEEK_END)
                return self._bytes_file.tell()

    def get_entry(self, name, default=None):
        assert self.is_dir, 'must be a directory'
        return self._dir.get(name)

    def set_entry(self, name, dir_entry):
        self._dir[name] = dir_entry

    def remove_entry(self, name):
        del self._dir[name]

    def __contains__(self, name):
        return name in self._dir

    def __len__(self):
        return len(self._dir)

    def list(self):
        return list(self._dir.keys())

    def add_open_file(self, memory_file):
        self._open_files.append(memory_file)

    def remove_open_file(self, memory_file):
        self._open_files.remove(memory_file)


@six.python_2_unicode_compatible
class MemoryFS(FS):
    """
    An in-memory filesystem.

    """

    _meta = {
        'case_insensitive': False,
        'invalid_path_chars': '\0',
        'network': False,
        'read_only': False,
        'thread_safe': True,
        'unicode_paths': True,
        'virtual': False,
    }

    def __init__(self, thread_safe=True):
        """
        Create an in-memory filesystem.

        """
        self._meta = self._meta.copy()
        self.thread_safe = bool(thread_safe)
        self._lock = RLock()
        self.root = self._make_dir_entry(ResourceType.directory, '')

    def __repr__(self):
        return "MemoryFS()".format(self.thread_safe)

    def __str__(self):
        return "<memfs>"

    def _make_dir_entry(self, *args, **kwargs):
        return _DirEntry(*args, **kwargs)

    def _normpath(self, path):
        path = abspath(normpath(path))
        self.validatepath(path)
        return path

    def _get_dir_entry(self, dir_path):
        """Get a directory entry, or None if one doesn't exist."""
        with self._lock:
            dir_path = normpath(dir_path)
            current_entry = self.root
            for path_component in iteratepath(dir_path):
                if not current_entry.is_dir:
                    return None
                current_entry = current_entry.get_entry(path_component)
                if current_entry is None:
                    return None
            return current_entry

    def _on_close_file(self, mem_file, path):
        dir_entry = self._get_dir_entry(path)
        if dir_entry is not None:
            dir_entry.remove_open_file(mem_file)

    def _on_access_file(self, path, time):
        dir_entry = self._get_dir_entry(path)
        dir_entry.accessed_time = time

    def _on_modify_file(self, path, time):
        dir_entry = self._get_dir_entry(path)
        dir_entry.accessed_time = dir_entry.modified_time = time

    def getinfo(self, path, namespaces=None):
        self._check()
        namespaces = namespaces or ()
        dir_entry = self._get_dir_entry(path)
        if dir_entry is None:
            raise errors.ResourceNotFound(path)
        info = {
            'basic': {
                'name': dir_entry.name,
                'is_dir': dir_entry.is_dir
            }
        }
        if 'details' in namespaces:
            info['details'] = {
                "_write": ['accessed', 'modified'],
                "type": int(dir_entry.resource_type),
                "size": dir_entry.size,
                "accessed": dir_entry.accessed_time,
                "modified": dir_entry.modified_time,
                "created": dir_entry.created_time,
            }
        return Info(info)

    def listdir(self, path):
        self._check()
        _path = self._normpath(path)
        with self._lock:
            dir_entry = self._get_dir_entry(_path)
            if dir_entry is None:
                raise errors.ResourceNotFound(path)
            if not dir_entry.is_dir:
                raise errors.DirectoryExpected(path)
            return dir_entry.list()

    def makedir(self, path, permissions=None, recreate=False):
        self._check()
        _path = abspath(self._normpath(path))
        with self._lock:
            if _path == '/':
                if recreate:
                    return self.opendir(path)
                else:
                    raise errors.DirectoryExists(path)

            dir_path, dir_name = split(_path)

            parent_dir = self._get_dir_entry(dir_path)
            if parent_dir is None:
                raise errors.ResourceNotFound(path)

            dir_entry = parent_dir.get_entry(dir_name)
            if dir_entry is not None and not recreate:
                raise errors.DirectoryExists(path)

            if dir_entry is None:
                new_dir = self._make_dir_entry(
                    ResourceType.directory,
                    dir_name
                )
                parent_dir.set_entry(dir_name, new_dir)
            return self.opendir(path)

    def openbin(self, path, mode="r", buffering=-1, **options):
        validate_openbin_mode(mode)
        self._check()
        _path = self._normpath(path)
        dir_path, file_name = split(_path)

        with self._lock:
            parent_dir_entry = self._get_dir_entry(dir_path)
            if parent_dir_entry is None or not parent_dir_entry.is_dir:
                raise errors.ResourceNotFound(path)

            if 'r' in mode or 'a' in mode:
                if file_name not in parent_dir_entry:
                    raise errors.ResourceNotFound(path)

                file_dir_entry = parent_dir_entry.get_entry(file_name)
                if file_dir_entry.is_dir:
                    raise errors.FileExpected(path)

                mem_file = _MemoryFile(
                    path=_path,
                    memory_fs=self,
                    bytes_io=file_dir_entry.bytes_file,
                    mode=mode,
                    lock=file_dir_entry._lock
                )
                file_dir_entry.add_open_file(mem_file)
                return mem_file

            if 'w' in mode:
                if file_name not in parent_dir_entry:
                    file_dir_entry = self._make_dir_entry(
                        ResourceType.file,
                        file_name
                    )
                    parent_dir_entry.set_entry(file_name, file_dir_entry)
                else:
                    file_dir_entry = self._get_dir_entry(_path)

                if file_dir_entry.is_dir:
                    raise errors.FileExpected(path)

                mem_file = _MemoryFile(
                    path=_path,
                    memory_fs=self,
                    bytes_io=file_dir_entry.bytes_file,
                    mode=mode,
                    lock=file_dir_entry._lock
                )
                file_dir_entry.add_open_file(mem_file)
                return mem_file

    def remove(self, path):
        self._check()
        _path = self._normpath(path)

        with self._lock:
            dir_path, file_name = split(_path)
            parent_dir_entry = self._get_dir_entry(dir_path)

            if parent_dir_entry is None or file_name not in parent_dir_entry:
                raise errors.ResourceNotFound(path)

            file_dir_entry = self._get_dir_entry(_path)
            if file_dir_entry.is_dir:
                raise errors.FileExpected(path)

            parent_dir_entry.remove_entry(file_name)

    def removedir(self, path, force=False):
        self._check()
        _path = self._normpath(path)

        if _path == '/':
            raise errors.RemoveRootError()

        with self._lock:
            dir_path, file_name = split(_path)
            parent_dir_entry = self._get_dir_entry(dir_path)

            if parent_dir_entry is None or file_name not in parent_dir_entry:
                raise errors.ResourceNotFound(path)

            dir_dir_entry = self._get_dir_entry(_path)
            if not dir_dir_entry.is_dir:
                raise errors.DirectoryExpected(path)

            if len(dir_dir_entry):
                raise errors.DirectoryNotEmpty(path)

            parent_dir_entry.remove_entry(file_name)

    def setinfo(self, path, info):
        self._check()
        _path = self._normpath(path)
        with self._lock:
            dir_path, file_name = split(_path)
            parent_dir_entry = self._get_dir_entry(dir_path)

            if parent_dir_entry is None or file_name not in parent_dir_entry:
                raise errors.ResourceNotFound(path)

            resource_entry = parent_dir_entry.get_entry(file_name)

            if 'details' in info:
                details = info['details']
                if 'accessed' in details:
                    resource_entry.accessed_time = details['accessed']
                if 'modified' in details:
                    resource_entry.modified_time = details['modified']
