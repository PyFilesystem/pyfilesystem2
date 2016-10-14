"""
Tools for managing mode strings (as used in :meth:`fs.base.FS.open` and
:meth:`fs.base.FS.openbin`).

"""

from __future__ import print_function
from __future__ import unicode_literals


def check_readable(mode):
    """
    Check a mode string allows reading.

    :param mode: A mode string, e.g. ``"rt"``
    :type mode: str
    :rtype: bool

    """
    if 'r' not in mode and '+' not in mode:
        return False
    return True


def check_writable(mode):
    """
    Check a mode string allows writing.

    :param mode: A mode string, e.g. ``"wt"``
    :type mode: str
    :rtype: bool

    """
    if 'r' in mode:
        return '+' in mode
    return True


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
