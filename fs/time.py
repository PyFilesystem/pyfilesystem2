"""Time related tools.
"""

from __future__ import print_function, unicode_literals

import typing

from calendar import timegm
from datetime import datetime

try:
    from datetime import timezone
except ImportError:
    from ._tzcompat import timezone  # type: ignore

if typing.TYPE_CHECKING:
    from typing import Optional


def datetime_to_epoch(d):
    # type: (datetime) -> int
    """Convert datetime to epoch."""
    return timegm(d.utctimetuple())


@typing.overload
def epoch_to_datetime(t):  # noqa: D103
    # type: (None) -> None
    pass


@typing.overload
def epoch_to_datetime(t):  # noqa: D103
    # type: (int) -> datetime
    pass


def epoch_to_datetime(t):
    # type: (Optional[int]) -> Optional[datetime]
    """Convert epoch time to a UTC datetime."""
    if t is None:
        return None
    return datetime.fromtimestamp(t, tz=timezone.utc)
