from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

from copy import deepcopy

from .path import join
from .enums import ResourceType
from .errors import MissingInfoNamespace
from .permissions import Permissions
from .time import epoch_to_datetime


class Info(object):
    """
    Container for :ref:`info`, returned by the following methods:

     * :meth:`~fs.base.FS.getinfo`
     * :meth:`~fs.base.FS.scandir`
     * :meth:`~fs.base.FS.filterfir`

    :param dict raw_info: A dict containing resource info.
    :param to_datetime: A callable that converts an epoch time to a
        datetime object. The default uses
        :func:`~fs.time.epoch_to_datetime`.

    """

    def __init__(self,
                 raw_info,
                 to_datetime=epoch_to_datetime):
        """
        Create a resource info object from a raw info dict.

        """
        self.raw = raw_info
        self._to_datetime = to_datetime
        self.namespaces = frozenset(self.raw.keys())

    def __repr__(self):
        if self.is_dir:
            return "<dir '{}'>".format(self.name)
        else:
            return "<file '{}'>".format(self.name)

    def __eq__(self, other):
        return self.raw == other.raw

    def _make_datetime(self, t):
        if t is not None:
            return self._to_datetime(t)
        else:
            return None

    def get(self, namespace, key, default=None):
        """
        Get a raw info value.

        >>> info.get('access', 'permissions')
        ['u_r', 'u_w', '_wx']

        :param str namespace: A namespace identifier.
        :param str key: A key within the namespace.
        :param default: A default value to return if either the
            namespace or namespace + key is not found.
        """
        try:
            return self.raw[namespace].get(key, default)
        except KeyError:
            return default

    def _require_namespace(self, namespace):
        """
        Raise a MissingInfoNamespace if the given namespace is not
        present in the info.

        """
        if namespace not in self.raw:
            raise MissingInfoNamespace(namespace)

    def is_writeable(self, namespace, key):
        """
        Check if a given key in a namespace is writable (with
        :meth:`~fs.base.FS.setinfo`).

        :param namespace: A namespace identifier.
        :type namespace: str
        :param key: A key within the namespace.
        :type key: str
        :rtype: bool

        """
        _writeable = self.get(namespace, '_write', ())
        return key in _writeable

    def has_namespace(self, namespace):
        """
        Check if the resource info contains a given namespace.

        :param namespace: A namespace name.
        :type namespace: str
        :rtype: bool

        """
        return namespace in self.raw

    def copy(self, to_datetime=None):
        """Create a copy of this resource info object."""
        return Info(
            deepcopy(self.raw),
            to_datetime=to_datetime or self._to_datetime
        )

    def make_path(self, dir_path):
        """
        Make a path by joining ``dir_path`` with the resource name.

        :param dir_path: A path to a directory.
        :type dir_path: str
        :returns: A path.
        :rtype: str

        """
        return join(dir_path, self.name)

    @property
    def name(self):
        """
        Get the resource name.

        :rtype: str

        """
        return self.get('basic', 'name')

    @property
    def is_dir(self):
        """
        Check if the resource references a directory.

        :rtype: bool

        """
        return self.get('basic', 'is_dir')

    @property
    def is_file(self):
        """
        Check if a resource references a file.

        :rtype: bool

        """
        return not self.get('basic', 'is_dir')

    @property
    def is_link(self):
        """
        Check if a resource is a symlink.

        :rtype: bool

        """
        self._require_namespace('link')
        return self.get('link', 'target') is not None

    @property
    def type(self):
        """
        Get the resource type enumeration.

        Requires the ``"details"`` namespace.

        :type: :class:`~fs.ResourceType`
        :raises ~fs.errors.MissingInfoNamespace: if the 'details'
            namespace is not in the Info.

        """
        self._require_namespace('details')
        return ResourceType(self.get('details', 'type', 0))

    @property
    def accessed(self):
        """
        Get the time this resource was last accessed, or ``None`` if not
        available.

        Requires the ``"details"`` namespace.

        :rtype: datetime
        :raises ~fs.errors.MissingInfoNamespace: if the 'details'
            namespace is not in the Info.

        """
        self._require_namespace('details')
        _time = self._make_datetime(
            self.get('details', 'accessed')
        )
        return _time

    @property
    def modified(self):
        """
        Get the time the resource was modified, or ``None`` if not
        available.

        Requires the ``"details"`` namespace.

        :rtype: datetime
        :raises ~fs.errors.MissingInfoNamespace: if the 'details'
            namespace is not in the Info.

        """
        self._require_namespace('details')
        _time = self._make_datetime(
            self.get('details', 'modified')
        )
        return _time

    @property
    def created(self):
        """
        Get the time this resource was created, or ``None`` if not
        available.

        Requires the ``"details"`` namespace.

        :rtype: datetime
        :raises ~fs.errors.MissingInfoNamespace: if the 'details'
            namespace is not in the Info.

        """
        self._require_namespace('details')
        _time = self._make_datetime(
            self.get('details', 'created')
        )
        return _time

    @property
    def metadata_changed(self):
        """
        Get the time the metadata changed, or ``None`` if not
        available.

        Requires the ``"details"`` namespace.

        :rtype: datetime
        :raises ~fs.errors.MissingInfoNamespace: if the 'details'
            namespace is not in the Info.

        """
        self._require_namespace('details')
        _time = self._make_datetime(
            self.get('details', 'metadata_changed')
        )
        return _time

    @property
    def permissions(self):
        """
        Get a permissions object, or ``None`` if not available.

        Requires the ``"access"`` namespace.

        :rtype: :class:`fs.permissions.Permissions`
        :raises ~fs.errors.MissingInfoNamespace: if the 'access'
            namespace is not in the Info.

        """
        self._require_namespace('access')
        _perm_names = self.get('access', 'permissions')
        if _perm_names is None:
            return None
        permissions = Permissions(_perm_names)
        return permissions

    @property
    def size(self):
        """
        Get the size of the resource, in bytes.

        Requires the ``"details"`` namespace.

        :rtype: int
        :raises ~fs.errors.MissingInfoNamespace: if the 'details'
            namespace is not in the Info.

        """
        self._require_namespace('details')
        return self.get('details', 'size')

    @property
    def user(self):
        """
        Get the owner of a resource, or ``None`` if not available.

        Requires the ``"access"`` namespace.

        :rtype: str
        :raises ~fs.errors.MissingInfoNamespace: if the 'access'
            namespace is not in the Info.

        """
        self._require_namespace('access')
        return self.get('access', 'user')

    @property
    def uid(self):
        """
        Get the user id of a resource, or ``None`` if not available.

        Requires the ``"access"`` namespace.

        :rtype: int
        :raises ~fs.errors.MissingInfoNamespace: if the 'access'
            namespace is not in the Info.

        """
        self._require_namespace('access')
        return self.get('access', 'uid')

    @property
    def group(self):
        """
        Get the group of the resource owner, or ``None`` if not
        available.

        Requires the ``"access"`` namespace.

        :rtype: str
        :raises ~fs.errors.MissingInfoNamespace: if the 'access'
            namespace is not in the Info.

        """
        self._require_namespace('access')
        return self.get('access', 'group')

    @property
    def gid(self):
        """
        Get the group id of a resource, or ``None`` if not available.

        Requires the ``"access"`` namespace.

        :rtype: int
        :raises ~fs.errors.MissingInfoNamespace: if the 'access'
            namespace is not in the Info.

        """
        self._require_namespace('access')
        return self.get('access', 'gid')

    @property
    def target(self):
        """
        Get the link target, if this is a symlink, or ``None`` if this
        is not a symlink.

        Requires the ``"link"`` namespace.

        :rtype: bool
        :raises ~fs.errors.MissingInfoNamespace: if the 'link'
            namespace is not in the Info.

        """
        self._require_namespace('link')
        return self.get('link', 'target')
