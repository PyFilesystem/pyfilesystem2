from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import unicodedata
import datetime
import re
import time

from pytz import UTC

from .enums import ResourceType
from .permissions import Permissions


EPOCH_DT = datetime.datetime.fromtimestamp(0, UTC)


RE_LINUX = re.compile(
    r"""
    ^
    ([ldrwx-]{10})
    \s+?
    (\d+)
    \s+?
    ([\w\-]+)
    \s+?
    ([\w\-]+)
    \s+?
    (\d+)
    \s+?
    (\w{3}\s+\d{1,2}\s+[\w:]+)
    \s+
    (.*?)
    $
    """,
    re.VERBOSE,
)


RE_WINDOWSNT = re.compile(
    r"""
    ^
    (?P<modified_date>\S+)
    \s+
    (?P<modified_time>\S+(AM|PM)?)
    \s+
    (?P<size>(<DIR>|\d+))
    \s+
    (?P<name>.*)
    $
    """,
    re.VERBOSE,
)


def get_decoders():
    """
    Returns all available FTP LIST line decoders with their matching regexes.
    """
    decoders = [
        (RE_LINUX, decode_linux),
        (RE_WINDOWSNT, decode_windowsnt),
    ]
    return decoders


def parse(lines):
    info = []
    for line in lines:
        if not line.strip():
            continue
        raw_info = parse_line(line)
        if raw_info is not None:
            info.append(raw_info)
    return info


def parse_line(line):
    for line_re, decode_callable in get_decoders():
        match = line_re.match(line)
        if match is not None:
            return decode_callable(line, match)
    return None


def _parse_time(t, formats):
    for frmt in formats:
        try:
            _t = time.strptime(t, frmt)
            break
        except ValueError:
            continue
    else:
        return None

    year = _t.tm_year if _t.tm_year != 1900 else time.localtime().tm_year
    month = _t.tm_mon
    day = _t.tm_mday
    hour = _t.tm_hour
    minutes = _t.tm_min
    dt = datetime.datetime(year, month, day, hour, minutes, tzinfo=UTC)

    epoch_time = (dt - EPOCH_DT).total_seconds()
    return epoch_time


def _decode_linux_time(mtime):
    return _parse_time(mtime, formats=["%b %d %Y", "%b %d %H:%M"])


def decode_linux(line, match):
    perms, links, uid, gid, size, mtime, name = match.groups()
    is_link = perms.startswith("l")
    is_dir = perms.startswith("d") or is_link
    if is_link:
        name, _, _link_name = name.partition("->")
        name = name.strip()
        _link_name = _link_name.strip()
    permissions = Permissions.parse(perms[1:])

    mtime_epoch = _decode_linux_time(mtime)

    name = unicodedata.normalize("NFC", name)

    raw_info = {
        "basic": {"name": name, "is_dir": is_dir},
        "details": {
            "size": int(size),
            "type": int(ResourceType.directory if is_dir else ResourceType.file),
        },
        "access": {"permissions": permissions.dump()},
        "ftp": {"ls": line},
    }
    access = raw_info["access"]
    details = raw_info["details"]
    if mtime_epoch is not None:
        details["modified"] = mtime_epoch

    access["user"] = uid
    access["group"] = gid

    return raw_info


def _decode_windowsnt_time(mtime):
    return _parse_time(mtime, formats=["%d-%m-%y %I:%M%p", "%d-%m-%y %H:%M"])


def decode_windowsnt(line, match):
    """
    Decodes a Windows NT FTP LIST line like one of these:

    `11-02-18  02:12PM       <DIR>          images`
    `11-02-18  03:33PM                 9276 logo.gif`

    Alternatively, the time (02:12PM) might also be present in 24-hour format (14:12).
    """
    is_dir = match.group("size") == "<DIR>"

    raw_info = {
        "basic": {
            "name": match.group("name"),
            "is_dir": is_dir,
        },
        "details": {
            "type": int(ResourceType.directory if is_dir else ResourceType.file),
        },
        "ftp": {"ls": line},
    }

    if not is_dir:
        raw_info["details"]["size"] = int(match.group("size"))

    modified = _decode_windowsnt_time(
        match.group("modified_date") + " " + match.group("modified_time")
    )
    if modified is not None:
        raw_info["details"]["modified"] = modified

    return raw_info
