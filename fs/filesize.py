"""
fs.filesize
===========

Functions for reporting filesizes

"""

from __future__ import division
from __future__ import unicode_literals

__all__ = ['traditional', 'decimal']



def _to_str(size, suffixes, base):
    try:
        size = int(size)
    except ValueError:
        raise ValueError(
            "filesize requires a numeric value, not {!r}".format(size)
        )
    if size == 1:
        return '1 byte'
    elif size < base:
        return '{:,} bytes'.format(size)

    for i, suffix in enumerate(suffixes, 2):
        unit = base ** i
        if size < unit:
            break
    return "{:,.1f} {}".format((base * size / unit), suffix)


def traditional(size):
    """
    Convert a filesize in to a string representation with traditional
    (base 2) units.

    :param int size: A file size.
    :returns: A string containing a abbreviated file size and units.
    :rtype str:

    """
    return _to_str(
        size,
        ('KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'),
        1024
    )


def decimal(size):
    """
    Convert a filesize in to a string representation with decimal
    units.

    :param int size: A file size.
    :returns: A string containing a abbreviated file size and units.
    :rtype str:
    """

    return _to_str(
        size,
        ('kbit', 'Mbit', 'Gbit', 'Tbit', 'Pbit', 'Ebit', 'Zbit', 'Ybit'),
        1000
    )
