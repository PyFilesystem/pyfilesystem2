"""Compatibility shim for python2's lack of datetime.timezone.

This is the example code from the Python 2 documentation:
https://docs.python.org/2.7/library/datetime.html#tzinfo-objects
"""

from datetime import timedelta, tzinfo

ZERO = timedelta(0)


class UTC(tzinfo):
    """UTC"""

    def utcoffset(self, dt):
        return ZERO

    def tzname(self, dt):
        return "UTC"

    def dst(self, dt):
        return ZERO


utc = UTC()


class timezone:
    utc = utc
