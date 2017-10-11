"""Container for filesystem resource informations.
"""

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
    """Container for :ref:`info`.

    Resource informations are returned by the following methods:

         * `~fs.base.FS.getinfo`
         * `~fs.base.FS.scandir`
         * `~fs.base.FS.filterfir`

    Arguments:
        raw_info (dict): A dict containing resource info.
        to_datetime (callable, optional): A callable that converts an
            epoch time to a datetime object. The default uses
            :func:`~fs.time.epoch_to_datetime`.

    """

    def __init__(self,
                 raw_info,
                 to_datetime=epoch_to_datetime):
        """Create a resource info object from a raw info dict.
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
        """Get a raw info value.

        Arguments:
            namespace (str): A namespace identifier.
            key (str): A key within the namespace.
            default (object, optional): A default value to return
                if either the namespace or the key within the namespace
                is not found.

        Example:
            >>> info.get('access', 'permissions')
            ['u_r', 'u_w', '_wx']

        """
        try:
            return self.raw[namespace].get(key, default)
        except KeyError:
            return default

    def _require_namespace(self, namespace):
        """Check if the given namespace is present in the info.

        Raises:
            ~fs.errors.MissingInfoNamespace: if the given namespace is not
                present in the info.

        """
        if namespace not in self.raw:
            raise MissingInfoNamespace(namespace)

    def is_writeable(self, namespace, key):
        """Check if a given key in a namespace is writable.

        Uses `~fs.base.FS.setinfo`.

        Arguments:
            namespace (str): A namespace identifier.
            key (str): A key within the namespace.

        Returns:
            bool: `True` if the key can be modified, `False` otherwise.

        """
        _writeable = self.get(namespace, '_write', ())
        return key in _writeable

    def has_namespace(self, namespace):
        """Check if the resource info contains a given namespace.

        Arguments:
            namespace (str): A namespace identifier.

        Returns:
            bool: `True` if the namespace was found, `False` otherwise.

        """
        return namespace in self.raw

    def copy(self, to_datetime=None):
        """Create a copy of this resource info object.
        """
        return Info(
            deepcopy(self.raw),
            to_datetime=to_datetime or self._to_datetime
        )

    def make_path(self, dir_path):
        """Make a path by joining ``dir_path`` with the resource name.

        Arguments:
            dir_path (str): A path to a directory.

        Returns:
            str: A path to the resource.

        """
        return join(dir_path, self.name)

    @property
    def name(self):
        """`str`: the resource name.
        """
        return self.get('basic', 'name')

    @property
    def is_dir(self):
        """`bool`: `True` if the resource references a directory.
        """
        return self.get('basic', 'is_dir')

    @property
    def is_file(self):
        """`bool`: `True` if the resource references a file.
        """
        return not self.get('basic', 'is_dir')

    @property
    def is_link(self):
        """`bool`: `True` if the resource is a symlink.
        """
        self._require_namespace('link')
        return self.get('link', 'target') is not None

    @property
    def type(self):
        """`~fs.ResourceType`: the type of the resource.

        Requires the ``"details"`` namespace.

        Raises:
            ~fs.errors.MissingInfoNamespace: if the 'details'
                namespace is not in the Info.

        """
        self._require_namespace('details')
        return ResourceType(self.get('details', 'type', 0))

    @property
    def accessed(self):
        """`~datetime.datetime`: the resource last access time, or `None`.

        Requires the ``"details"`` namespace.

        Raises:
            ~fs.errors.MissingInfoNamespace: if the ``"details"``
                namespace is not in the Info.

        """
        self._require_namespace('details')
        _time = self._make_datetime(
            self.get('details', 'accessed')
        )
        return _time

    @property
    def modified(self):
        """`~datetime.datetime`: the resource last modification time, or `None`.

        Requires the ``"details"`` namespace.

        Raises:
            ~fs.errors.MissingInfoNamespace: if the ``"details"``
                namespace is not in the Info.

        """
        self._require_namespace('details')
        _time = self._make_datetime(
            self.get('details', 'modified')
        )
        return _time

    @property
    def created(self):
        """`~datetime.datetime`: the resource creation time, or `None`.

        Requires the ``"details"`` namespace.

        Raises:
            ~fs.errors.MissingInfoNamespace: if the ``"details"``
                namespace is not in the Info.

        """
        self._require_namespace('details')
        _time = self._make_datetime(
            self.get('details', 'created')
        )
        return _time

    @property
    def metadata_changed(self):
        """`~datetime.datetime`: the resource metadata change time, or `None`.

        Requires the ``"details"`` namespace.

        Raises:
            ~fs.errors.MissingInfoNamespace: if the ``"details"``
                namespace is not in the Info.

        """
        self._require_namespace('details')
        _time = self._make_datetime(
            self.get('details', 'metadata_changed')
        )
        return _time

    @property
    def permissions(self):
        """`Permissions`: the permissions of the resource, or `None`.

        Requires the ``"access"`` namespace.

        Raises:
            ~fs.errors.MissingInfoNamespace: if the ``"access"``
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
        """`int`: the size of the resource, in bytes.

        Requires the ``"details"`` namespace.

        Raises:
            ~fs.errors.MissingInfoNamespace: if the ``"details"``
                namespace is not in the Info.

        """
        self._require_namespace('details')
        return self.get('details', 'size')

    @property
    def user(self):
        """`str`: the owner of the resource, or `None`.

        Requires the ``"access"`` namespace.

        Raises:
            ~fs.errors.MissingInfoNamespace: if the ``"access"``
                namespace is not in the Info.

        """
        self._require_namespace('access')
        return self.get('access', 'user')

    @property
    def uid(self):
        """`int`: the user id of the resource, or `None`.

        Requires the ``"access"`` namespace.

        Raises:
            ~fs.errors.MissingInfoNamespace: if the ``"access"``
                namespace is not in the Info.

        """
        self._require_namespace('access')
        return self.get('access', 'uid')

    @property
    def group(self):
        """`str`: the group of the resource owner, or `None`.

        Requires the ``"access"`` namespace.

        Raises:
            ~fs.errors.MissingInfoNamespace: if the ``"access"``
                namespace is not in the Info.

        """
        self._require_namespace('access')
        return self.get('access', 'group')

    @property
    def gid(self):
        """`int`: the group id of the resource, or `None`.

        Requires the ``"access"`` namespace.

        Raises:
            ~fs.errors.MissingInfoNamespace: if the ``"access"``
                namespace is not in the Info.

        """
        self._require_namespace('access')
        return self.get('access', 'gid')

    @property
    def target(self):  # noqa: D402
        """`str`: the link target (if resource is a symlink), or `None`.

        Requires the ``"link"`` namespace.

        Raises:
            ~fs.errors.MissingInfoNamespace: if the ``"link"``
                namespace is not in the Info.

        """
        self._require_namespace('link')
        return self.get('link', 'target')
