import io
# from six.moves import http_cookiejar, http_client
# from six.moves.urllib import parse as urllib_parse
import six
import threading

import webdav.client as wc
import webdav.exceptions as we
import webdav.urn as wu

from . import errors
from .base import FS
from .enums import ResourceType, Seek
from .info import Info
from .iotools import line_iterator
from .mode import Mode
from .path import abspath, normpath

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

        self._lock = threading.RLock()
        self.pos = 0
        self.closed = False

        if 'a' in mode:
            try:
                self.pos = self.fs.getsize(self.path)
            except errors.ResourceNotFound:
                self.pos = 0

    def __repr__(self):
        _repr = "WebDAVFile({!r}, {!r}, {!r})"
        return _repr.format(self.fs, self.path, self.mode)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def __iter__(self):
        return line_iterator(self)

    def close(self):
        if not self.closed:
            self.closed = True

    def flush(self):
        pass

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

    def read(self):
        with self._lock:
            data_file = io.BytesIO()

            self.res.write_to(data_file)

            data_bytes = data_file.getvalue()
            return data_bytes

    def seek(self, pos, whence=Seek.set):
        if whence == Seek.set:
            self.pos = pos
        elif whence == Seek.current:
            self.pos = self.pos + pos
        elif whence == Seek.end:
            self.pos = max(0, self.fs.getsize(self.path) + pos)
        else:
            raise ValueError('invalid value for whence')

    def tell(self):
        return self.pos

    def write(self, data):
        if self.pos > 0:
            previous_data = self.read()
            data_file = io.BytesIO(previous_data)
            data_file.seek(self.pos)
            data_file.write(data)
            data_file.seek(io.SEEK_SET)
        else:
            data_file = io.BytesIO(data)

        self.res.read_from(data_file)

    def writelines(self, lines):
        self.write(b''.join(lines))


class WebDAVFS(FS):
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
                info_dict['basic'][key] = val
            elif key in details:
                if key == 'size' and val:
                    val = int(val)
                info_dict['details'][key] = val
            elif key in access:
                info_dict['access'][key] = val
            else:
                info_dict['other'][key] = val

        return info_dict

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
            if self.client.is_dir(path):
                info_dict['basic']['is_dir'] = True
                info_dict['details']['type'] = int(ResourceType.directory)
            return Info(info_dict)
        except we.RemoteResourceNotFound:
            raise errors.ResourceNotFound(path)

    def listdir(self, path):
        if not self.client.check(path):
            raise errors.ResourceNotFound(path)
        if path in ('.', './'):
            return self.client.list('/')
        return self.client.list(path)

    def makedir(self, path, permissions=None, recreate=False):
        self.client.mkdir(path)

    def openbin(self, path, mode='r', buffering=-1, **options):
        _mode = Mode(mode)
        _mode.validate_bin()
        self.check()
        self.validatepath(path)
        buf = io.BytesIO()

        with self._lock:
            try:
                info = self.getinfo(path)
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
        if not self.client.check(path):
            raise errors.ResourceNotFound(path)

        if self.client.is_dir(path):
            raise errors.FileExpected(path)

        self.client.clean(path)

    def removedir(self, path):
        if path == '/':
            raise errors.RemoveRootError

        if not self.client.check(path):
            raise errors.ResourceNotFound(path)

        if not self.client.is_dir(path):
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
        pass
