# from six.moves import http_cookiejar, http_client
# from six.moves.urllib import parse as urllib_parse
import six

import webdav.client as wc
import webdav.exceptions as we

from .base import FS
from .enums import ResourceType
from .errors import ResourceNotFound
from .info import Info

basics = frozenset(['name'])
details = frozenset(('type', 'accessed', 'modified', 'created',
                     'metadata_changed', 'size'))
access = frozenset(('permissions', 'user', 'uid', 'group', 'gid'))


class WebDAVFS(FS):
    def __init__(self, url, credentials=None, root=None):
        if not url.endswith("/"):
            url += "/"
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

    @staticmethod
    def _create_info_dict(info):
        info_dict = {'basic': {"is_dir": False}, 'details': {}, 'access': {}}

        for key, val in six.iteritems(info):
            if key in basics:
                info_dict['basic'][key] = val
            elif key in details:
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
            return Info(info_dict)
        except we.RemoteResourceNotFound:
            raise ResourceNotFound(path)

    def listdir(self, path):
        return self.client.list(path)

    def makedir(self, path, permissions=None, recreate=False):
        self.client.mkdir(path)

    def openbin(self, path, mode='r', buffering=-1, **options):
        return open(path, mode, buffering, **options)

    def remove(self, path):
        pass

    def removedir(self, path):
        pass

    def setinfo(self, path, info):
        pass
