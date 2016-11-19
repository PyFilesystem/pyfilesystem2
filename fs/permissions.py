"""
An abstract permissions container.

"""

from __future__ import print_function
from __future__ import unicode_literals

import six


def make_mode(init):
    """
    Make a mode integer from an initial value.

    """
    return Permissions.get_mode(init)


class _PermProperty(object):
    """Creates simple properties to get/set permissions."""
    def __init__(self, name):
        self._name = name
        self.__doc__ = "Boolean for '{}' permission.".format(name)

    def __get__(self, obj, obj_type=None):
        return self._name in obj

    def __set__(self, obj, value):
        if value:
            obj.add(self._name)
        else:
            obj.remove(self._name)


@six.python_2_unicode_compatible
class Permissions(object):
    """
    An abstraction for file system permissions.

    :param list names: A list of permissions.
    :param int mode: A mode integer.
    :param str user: A triplet of *user* permissions, e.g. ``"rwx"`` or
        ``"r--"``
    :param str group: A triplet of *group* permissions, e.g. ``"rwx"``
        or ``"r--"``
    :param str other: A triplet of *other* permissions, e.g. ``"rwx"``
        or ``"r--"``
    :param bool sticky: A boolean for the *sticky* bit.
    :param bool setuid: A boolean for the *setuid* bit.
    :param bool setguid: A boolean for the *setuid* bit.

    Permissions objects store information regarding the permissions
    on a resource. It supports Linux permissions, but is generic enough
    to manage permission information from almost any filesystem.

    >>> from fs.permissions import Permissions
    >>> p = Permissions(user='rwx', group='rw-', other='r--')
    >>> print(p)
    rwxrw-r--
    >>> p.mode
    500
    >>> oct(p.mode)
    '0764'



    """

    _LINUX_PERMS = [
        ('setuid', 2048),
        ('setguid', 1024),
        ('sticky', 512),
        ('u_r', 256),
        ('u_w', 128),
        ('u_x', 64),
        ('g_r', 32),
        ('g_w', 16),
        ('g_x', 8),
        ('o_r', 4),
        ('o_w', 2),
        ('o_x', 1)
    ]
    _LINUX_PERMS_NAMES = [_name for _name, _mask in _LINUX_PERMS]

    def __init__(self,
                 names=None,
                 mode=None,
                 user=None,
                 group=None,
                 other=None,
                 sticky=None,
                 setuid=None,
                 setguid=None):
        if names is not None:
            self._perms = set(names)
        elif mode is not None:
            self._perms = {
                name
                for name, mask in self._LINUX_PERMS
                if mode & mask
            }
        else:
            perms = self._perms = set()
            perms.update('u_' + p for p in user or '' if p != '-')
            perms.update('g_' + p for p in group or '' if p != '-')
            perms.update('o_' + p for p in other or '' if p != '-')

        if sticky:
            self._perms.add('sticky')
        if setuid:
            self._perms.add('setuid')
        if setguid:
            self._perms.add('setguid')

    def __repr__(self):
        if not self._perms.issubset(self._LINUX_PERMS_NAMES):
            _perms_str = ", ".join(
                "'{}'".format(p) for p in sorted(self._perms)
            )
            return "Permissions(names=[{}])".format(_perms_str)

        def _check(perm, name):
            return name if perm in self._perms else ''

        user = ''.join((
            _check('u_r', 'r'),
            _check('u_w', 'w'),
            _check('u_x', 'x')
        ))
        group = ''.join((
            _check('g_r', 'r'),
            _check('g_w', 'w'),
            _check('g_x', 'x')
        ))
        other = ''.join((
            _check('o_r', 'r'),
            _check('o_w', 'w'),
            _check('o_x', 'x')
        ))
        args = []
        _fmt = "user='{}', group='{}', other='{}'"
        basic = _fmt.format(user, group, other)
        args.append(basic)
        if self.sticky:
            args.append('sticky=True')
        if self.setuid:
            args.append('setuid=True')
        if self.setuid:
            args.append('setguid=True')
        return "Permissions({})".format(', '.join(args))

    def __str__(self):
        return self.as_str()

    def __iter__(self):
        return iter(self._perms)

    def __contains__(self, permission):
        return permission in self._perms

    def __eq__(self, other):
        if isinstance(other, Permissions):
            names = other.dump()
        else:
            names = other
        return self.dump() == names

    def __ne__(self, other):
        return not self.__eq__(other)

    @classmethod
    def parse(cls, ls):
        """Parse permissions in linux notation."""
        user = ls[:3]
        group = ls[3:6]
        other = ls[6:9]
        return cls(user=user, group=group, other=other)

    @classmethod
    def load(cls, permissions):
        """Load a serialized permissions object."""
        return cls(names=permissions)

    @classmethod
    def create(cls, init=None):
        """
        Create a permissions object from an initial value.

        :param init: May be None for equivalent for 0o777 permissions,
            a mode integer, or a list of permission names.
        :returns: mode integer, that may be used by `os.makedir`
            (amongst others).

        >>> Permissions.create(None)
        Permissions(user='rwx', group='rwx', other='rwx')
        >>> Permissions.create(0o700)
        Permissions(user='rwx', group='', other='')
        >>> Permissions.create(['u_r', 'u_w', 'u_x'])
        Permissions(user='rwx', group='', other='')

        """
        if init is None:
            return cls(mode=0o777)
        if isinstance(init, cls):
            return init
        if isinstance(init, int):
            return cls(mode=init)
        if isinstance(init, list):
            return cls(names=init)
        raise ValueError('permissions is invalid')

    @classmethod
    def get_mode(cls, init):
        """
        Convert an initial value to a mode integer.

        """
        return cls.create(init).mode

    def copy(self):
        """Make a copy of this permissions object."""
        return Permissions(names=list(self._perms))

    def dump(self):
        """Get a list suitable for serialization."""
        return sorted(self._perms)

    def as_str(self):
        """Get a linux-style string representation of permissions."""
        perms = [
            c if name in self._perms else '-'
            for name, c in zip(
                self._LINUX_PERMS_NAMES[-9:],
                'rwxrwxrwx'
            )
        ]
        if 'setuid' in self._perms:
            perms[2] = 's' if 'u_x' in self._perms else 'S'
        if 'setguid' in self._perms:
            perms[5] = 's' if 'g_x' in self._perms else 'S'
        if 'sticky' in self._perms:
            perms[8] = 't' if 'o_x' in self._perms else 'T'

        perm_str = ''.join(perms)
        return perm_str

    @property
    def mode(self):
        """Mode integer."""
        mode = 0
        for name, mask in self._LINUX_PERMS:
            if name in self._perms:
                mode |= mask
        return mode

    @mode.setter
    def mode(self, mode):
        """Set mode integer."""
        self._perms = {
            name
            for name, mask in self._LINUX_PERMS
            if mode & mask
        }

    u_r = _PermProperty('u_r')
    u_w = _PermProperty('u_w')
    u_x = _PermProperty('u_x')

    g_r = _PermProperty('g_r')
    g_w = _PermProperty('g_w')
    g_x = _PermProperty('g_x')

    o_r = _PermProperty('o_r')
    o_w = _PermProperty('o_w')
    o_x = _PermProperty('o_x')

    sticky = _PermProperty('sticky')
    setuid = _PermProperty('setuid')
    setguid = _PermProperty('setguid')

    def add(self, *permissions):
        """
        Add permission(s).

        :param permissions: Permission name(s).

        """
        self._perms.update(permissions)

    def remove(self, *permissions):
        """
        Remove permission(s).

        :param permissions: Permission name(s).

        """
        self._perms.difference_update(permissions)

    def check(self, *permissions):
        """
        Check if one or more permissions are enabled.

        :param permissions: Permission name(s).
        :returns: True if all given permissions are set.
        :rtype bool:

        """
        return self._perms.issuperset(permissions)
