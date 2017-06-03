from contextlib import closing
import io
import os
import six
import threading
import logging

# import webdav.client as wc
# import webdav.exceptions as we
# import webdav.urn as wu

import webdav2.client as wc
import webdav2.exceptions as we
import webdav2.urn as wu

from . import errors
from .base import FS
from .enums import ResourceType, Seek
from .info import Info
from .iotools import line_iterator
from .mode import Mode
from .path import abspath, normpath


log = logging.getLogger(__name__)

basics = frozenset(['name'])
details = frozenset(('type', 'accessed', 'modified', 'created',
                     'metadata_changed', 'size'))
access = frozenset(('permissions', 'user', 'uid', 'group', 'gid'))


class WebDAVFile(object):

    def __init__(self, wdfs, path, mode):
        self.fs = wdfs
        self.path = path
        self.res = self.fs.get_resource(self.path)
        self.mode = mode
        self._mode = Mode(mode)
        self._lock = threading.RLock()
        self.data = self._get_file_data()

        self.pos = 0
        self.closed = False

        if 'a' in mode:
            self.pos = self._get_data_size()

    def _get_file_data(self):
        with self._lock:
            data = io.BytesIO()
            try:
                self.res.write_to(data)
                if 'a' not in self.mode:
                    data.seek(io.SEEK_SET)
            except we.RemoteResourceNotFound:
                data.write(b'')

            return data

    def _get_data_size(self):
        if six.PY2:
            return len(self.data.getvalue())
        else:
            return self.data.getbuffer().nbytes

    def __repr__(self):
        _repr = "WebDAVFile({!r}, {!r}, {!r})"
        return _repr.format(self.fs, self.path, self.mode)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def __iter__(self):
        return line_iterator(self)

    def __del__(self):
        self.close()

    def close(self):
        if not self.closed:
            log.debug("closing")
            self.flush()
            self.data.close()
            self.closed = True

    def flush(self):
        if self._mode.writing:
            log.debug("flush")
            self.data.seek(io.SEEK_SET)
            self.res.read_from(self.data)

    def next(self):
        return self.readline()

    __next__ = next

    def readline(self, size=None):
        return next(line_iterator(self, size))

    def readlines(self, hint=-1):
        lines = []
        size = 0
        for line in line_iterator(self):
            lines.append(line)
            size += len(line)
            if hint != -1 and size > hint:
                break
        return lines

    def read(self, size=None):
        if not self._mode.reading   :
            raise IOError("File is not in read mode")
        if size:
            self.pos += size
        return self.data.read(size)

    def seek(self, pos, whence=Seek.set):
        if whence == Seek.set:
            self.pos = pos
        elif whence == Seek.current:
            self.pos = self.pos + pos
        elif whence == Seek.end:
            self.pos = max(0, self._get_data_size() + pos)
        else:
            raise ValueError('invalid value for whence')

        self.data.seek(self.pos)

    def tell(self):
        return self.pos

    def truncate(self, size=None):
        self.data.truncate(size)
        data_size = self._get_data_size()
        if size and data_size < size:
            self.data.write(b'\0' * (size - data_size))

    def write(self, data):
        if not self._mode.writing:
            raise IOError("File is not in write mode")
        self.data.write(data)
        self.seek(len(data), Seek.current)

    def writelines(self, lines):
        self.write(b''.join(lines))


class WebDAVFS(FS):

    _meta = {
        'case_insensitive': False,
        'invalid_path_chars': '\0',
        'network': True,
        'read_only': False,
        'thread_safe': True,
        'unicode_paths': True,
        'virtual': False,
    }

    def __init__(self, url, credentials=None, root=None):
        self.url = url
        self.credentials = credentials
        self.root = root
        super(WebDAVFS, self).__init__()

        options = {
            'webdav_hostname': self.url,
            'webdav_login': self.credentials["login"],
            'webdav_password': self.credentials["password"],
            'root': self.root
        }
        self.client = wc.Client(options)

    def _create_resource(self, path):
        urn = wu.Urn(path)
        res = wc.Resource(self.client, urn)
        return res

    def get_resource(self, path):
        return self._create_resource(path)

    @staticmethod
    def _create_info_dict(info):
        info_dict = {
            'basic': {"is_dir": False},
            'details': {'type': int(ResourceType.file)},
            'access': {}
        }

        for key, val in six.iteritems(info):
            if key in basics:
                info_dict['basic'][key] = six.u(val)
            elif key in details:
                if key == 'size' and val:
                    val = int(val)
                elif val:
                    val = six.u(val)
                info_dict['details'][key] = val
            elif key in access:
                info_dict['access'][key] = six.u(val)
            else:
                info_dict['other'][key] = six.u(val)

        return info_dict

    def isdir(self, path):
        try:
            return self.client.is_dir(path)
        except we.RemoteResourceNotFound:
            return False

    def exists(self, path):
        return self.client.check(path)

    def getinfo(self, path, namespaces=None):
        self.check()
        _path = self.validatepath(path)
        namespaces = namespaces or ()

        if _path == '/':
            return Info({
                "basic":
                {
                    "name": "",
                    "is_dir": True
                },
                "details":
                {
                    "type": int(ResourceType.directory)
                }
            })

        try:
            info = self.client.info(path)
            info_dict = self._create_info_dict(info)
            if self.isdir(path):
                info_dict['basic']['is_dir'] = True
                info_dict['details']['type'] = int(ResourceType.directory)
            return Info(info_dict)
        except we.RemoteResourceNotFound:
            raise errors.ResourceNotFound(path)

    def listdir(self, path):
        self.check()
        _path = self.validatepath(path)

        if not self.exists(_path):
            raise errors.ResourceNotFound(path)
        if not self.isdir(_path):
            raise errors.DirectoryExpected(path)

        dir_list = self.client.list(_path)
        if six.PY2:
            dir_list = [six.u(item) for item in dir_list]

        return dir_list

    def makedir(self, path, permissions=None, recreate=False):
        self.check()
        self.validatepath(path)
        _path = abspath(normpath(path))

        if _path == '/':
            if recreate:
                return self.opendir(path)
            else:
                raise errors.DirectoryExists(path)

        if not (recreate and self.isdir(path)):
            if self.exists(_path):
                raise errors.DirectoryExists(path)

            try:
                self.client.mkdir(_path)
            except we.RemoteParentNotFound:
                raise errors.ResourceNotFound(path)

        return self.opendir(path)

    def openbin(self, path, mode='r', buffering=-1, **options):
        _mode = Mode(mode)
        _mode.validate_bin()
        self.check()
        self.validatepath(path)

        log.debug("openbin: %s, %s", path, mode)
        with self._lock:
            try:
                info = self.getinfo(path)
                log.debug("Info: %s", info)
            except errors.ResourceNotFound:
                if _mode.reading:
                    raise errors.ResourceNotFound(path)
            else:
                if info.is_dir:
                    raise errors.FileExpected(path)
            if _mode.exclusive:
                raise errors.FileExists(path)
        wdfile = WebDAVFile(self, abspath(normpath(path)), mode)
        return wdfile

    def remove(self, path):
        if not self.exists(path):
            raise errors.ResourceNotFound(path)

        if self.isdir(path):
            raise errors.FileExpected(path)

        self.client.clean(path)

    def removedir(self, path):
        if path == '/':
            raise errors.RemoveRootError

        if not self.exists(path):
            raise errors.ResourceNotFound(path)

        if not self.isdir(path):
            raise errors.DirectoryExpected(path)

        checklist = self.client.list(path)
        if checklist:
            raise errors.DirectoryNotEmpty(path)

        self.client.clean(path)

    def setbytes(self, path, contents):
        if not isinstance(contents, bytes):
            raise ValueError('contents must be bytes')
        _path = abspath(normpath(path))
        self.validatepath(path)
        bin_file = io.BytesIO(contents)
        with self._lock:
            resource = self._create_resource(_path)
            resource.read_from(bin_file)

    def setinfo(self, path, info):
        if not self.exists(path):
            raise errors.ResourceNotFound(path)

    def create(self, path, wipe=False):
        with self._lock:
            if not wipe and self.exists(path):
                return False
            with self.open(path, 'wb') as new_file:
                # log.debug("CREATE %s", new_file)
                new_file.truncate(0)
            return True

    def copy(self, src_path, dst_path, overwrite=False):
        with self._lock:
            if not overwrite and self.exists(dst_path):
                raise errors.DestinationExists(dst_path)
            try:
                self.client.copy(src_path, dst_path)
            except we.RemoteResourceNotFound:
                raise errors.ResourceNotFound(src_path)
            except we.RemoteParentNotFound:
                raise errors.ResourceNotFound(dst_path)

    def move(self, src_path, dst_path, overwrite=False):
        if not overwrite and self.exists(dst_path):
            raise errors.DestinationExists(dst_path)
        with self._lock:
            try:
                self.client.move(src_path, dst_path, overwrite=overwrite)
            except we.RemoteResourceNotFound:
                raise errors.ResourceNotFound(src_path)
            except we.RemoteParentNotFound:
                raise errors.ResourceNotFound(dst_path)
