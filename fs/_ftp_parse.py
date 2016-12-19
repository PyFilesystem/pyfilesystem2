from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import re
import time
import calendar

from .enums import ResourceType
from .permissions import Permissions


re_linux = re.compile(
    """
    ^
    ([ldrwx-]{10})
    \s+?
    (\d+)
    \s+?
    (\w+)
    \s+?
    (\w+)
    \s+?
    (\d+)
    \s+?
    (\w{3}\s\d{2}\s+[\w:]+)
    \s+
    (.*?)
    $
    """,
    re.VERBOSE
)


def get_decoders():
    decoders = [
        (re_linux, decode_linux),
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


def _parse_time(t):

    t = ' '.join(token.strip() for token in t.lower().split(' '))

    try:
        try:
            _t = time.strptime(t, '%b %d %Y')
        except ValueError:
            _t = time.strptime(t, '%b %d %H:%M')
    except ValueError:
        # Unknown time format
        return None

    epoch_time = calendar.timegm((
        _t.tm_year if _t.tm_year != 1900 else time.localtime().tm_year,
        _t.tm_mon, _t.tm_mday - 1, _t.tm_hour, _t.tm_min, 0, 0, 0, 0, 'UTC'
    ))

    return epoch_time


def decode_linux(line, match):
    perms, links, uid, gid, size, mtime, name = match.groups()
    is_link = perms.startswith('l')
    is_dir = perms.startswith('d') or is_link
    if is_link:
        name, _, link_name = name.partition('->')
        name = name.strip()
        link_name = link_name.strip()
    permissions = Permissions.parse(perms[1:])

    mtime_epoch = _parse_time(mtime)

    raw_info = {
        "basic": {
            "name": name,
            "is_dir": is_dir
        },
        "details": {
            "size": int(size),
            "type": int(
                ResourceType.directory
                if is_dir else
                ResourceType.file
            )
        },
        "access": {
            "permissions": permissions.dump()
        },
        "ftp": {
            "ls": line
        }
    }
    access = raw_info['access']
    details = raw_info['details']
    if mtime_epoch is not None:
        details['modified'] = mtime_epoch

    access['user'] = uid
    access['group'] = gid

    return raw_info
