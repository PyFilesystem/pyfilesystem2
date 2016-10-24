"""
Tools for managing mode strings (as used in :meth:`fs.base.FS.open` and
:meth:`fs.base.FS.openbin`).

"""

from __future__ import print_function
from __future__ import unicode_literals

import six


# https://docs.python.org/3/library/functions.html#open
@six.python_2_unicode_compatible
class Mode(object):

    def __init__(self, mode):
        if not mode:
            raise ValueError('mode must not be empty')
        if mode[0] not in 'rwxa':
            raise ValueError(
                "mode must start with 'r', 'w', 'x', or 'a'"
            )
        if 't' in mode and 'b' in mode:
            raise ValueError(
                "mode can't be binary ('b') and text ('t')"
            )
        self._mode = mode

    def __repr__(self):
        return "Mode({!r})".format(self._mode)

    def __str__(self):
        return self._mode

    def __contains__(self, c):
        return c in self._mode

    @property
    def reading(self):
        return 'r' in self or '+' in self

    @property
    def writing(self):
        return 'w' in self or 'a' in self or '+' in self

    @property
    def updating(self):
        return '+' in self

    @property
    def truncate(self):
        return 'w' in self or 'x' in self

    @property
    def exclusive(self):
        return 'x' in self

    @property
    def binary(self):
        return 'b' in self

    @property
    def text(self):
        return 't' in self or 'b' not in self


def check_readable(mode):
    """
    Check a mode string allows reading.

    :param mode: A mode string, e.g. ``"rt"``
    :type mode: str
    :rtype: bool

    """
    return Mode(mode).reading


def check_writable(mode):
    """
    Check a mode string allows writing.

    :param mode: A mode string, e.g. ``"wt"``
    :type mode: str
    :rtype: bool

    """
    return Mode(mode).writing


def validate_open_mode(mode, _valid_chars=frozenset('rwabt+')):
    """
    Check ``mode`` parameter of :meth:`fs.base.FS.open` is valid.

    :param mode: Mode parameter.
    :type mode: str
    :raises: `ValueError` if mode is not valid.

    """
    if not mode:
        raise ValueError('mode must not be empty')
    if mode[0] not in 'rwa':
        raise ValueError("mode must start with 'r', 'w', or 'a'")
    if not _valid_chars.issuperset(mode):
        raise ValueError("mode '{}' contains invalid characters".format(mode))


def validate_openbin_mode(mode, _valid_chars=frozenset('rwab+')):
    """
    Check ``mode`` parameter of :meth:`fs.base.FS.openbin` is valid.

    :param mode: Mode parameter.
    :type mode: str
    :raises: `ValueError` if mode is not valid.

    """
    if 't' in mode:
        raise ValueError('text mode not valid in openbin')
    if not mode:
        raise ValueError('mode must not be empty')
    if mode[0] not in 'rwa':
        raise ValueError("mode must start with 'r', 'w', or 'a'")
    if not _valid_chars.issuperset(mode):
        raise ValueError("mode '{}' contains invalid characters".format(mode))
