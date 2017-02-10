# from six.moves import http_cookiejar, http_client
# from six.moves.urllib import parse as urllib_parse
import six
import threading

from .base import FS
from .errors import ResourceNotFound, PermissionDenied, RemoteConnectionError


class WebDAVFS(FS):
    connection_classes = {
        'http': six.moves.http_client.HTTPConnection,
        'https': six.moves.http_client.HTTPSConnection,
    }

    _DEFAULT_PORT_NUMBERS = {
        'http': 80,
        'https': 443,
    }

    _meta = {
        'virtual': False,
        'read_only': False,
        'unicode_paths': True,
        'case_insensitive_paths': False,
        'network': True
     }

    def __init__(self, url, credentials=None, get_credentials=None,
                 connection_classes=None, timeout=None):
        if not url.endswith("/"):
            url += "/"
        self.url = url
        self.timeout = timeout
        self.credentials = credentials
        self.get_credentials = get_credentials
        if connection_classes is not None:
            self.connection_classes = self.connection_classes.copy()
            self.connection_classes.update(connection_classes)
        self._connections = []
        self._free_connections = {}
        self._connection_lock = threading.Lock()
        self._cookiejar = six.moves.http_cookiejar.CookieJar()
        super(WebDAVFS, self).__init__()

        # resp = self._check_server_speaks_webdav()
        # self.url = resp.request_url
        self._url_p = six.moves.urllib.parse.urlparse(self.url)

    # def _check_server_speaks_webdav(self):
    #     pf = propfind(prop="<prop xmlns='DAV:'><resourcetype /></prop>")
    #     resp = self._request("/", "PROPFIND", pf.render(), {"Depth": "0"})
    #     try:
    #         if resp.status == 404:
    #             raise ResourceNotFound("/", msg="root url gives 404")
    #         if resp.status in (401, 403):
    #             raise PermissionDenied("listdir (http %s)" % resp.status)
    #         if resp.status != 207:
    #             msg = "server at %s doesn't speak WebDAV" % (self.url,)
    #             raise RemoteConnectionError(exc=resp.read(), msg=msg)
    #     finally:
    #         resp.close()
    #     return resp

    def getinfo(self, path, namespaces=None):
        pass

    def listdir(self, path):
        pass

    def makedir(self, path, permissions=None, recreate=False):
        pass

    def openbin(self, path, mode='r', buffering=-1, **options):
        pass

    def remove(self, path):
        pass

    def removedir(self, path):
        pass

    def setinfo(self, path, info):
        pass
