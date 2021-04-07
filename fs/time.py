"""Time related tools.
"""

from __future__ import print_function
from __future__ import unicode_literals

import typing
from calendar import timegm
from datetime import datetime
from pytz import UTC, timezone

if typing.TYPE_CHECKING:
    from typing import Optional


utcfromtimestamp = datetime.utcfromtimestamp
utclocalize = UTC.localize
GMT = timezone("GMT")


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
    return utclocalize(utcfromtimestamp(t)) if t is not None else None
