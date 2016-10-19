"""Match wildcard filenames."""
# Adapted from https://hg.python.org/cpython/file/2.7/Lib/fnmatch.py

from __future__ import unicode_literals

import re
from functools import partial

from .lrucache import LRUCache

_MAXCACHE = 1000
_cache = LRUCache(_MAXCACHE)


def match(pattern, name):
    """
    Test whether `name` matches wildcard pattern `patter`.

    :param pattern: A wildcard pattern. e.g. "*.py"
    :type pattern: str
    :param name: A filename
    :type name: str

    """
    try:
        re_pat = _cache[(pattern, True)]
    except KeyError:
        res = _translate(pattern)
        _cache[(pattern, True)] = re_pat = re.compile(res)
    return re_pat.match(name) is not None


def imatch(pattern, name):
    """
    Test whether `name` matches wildcard pattern `pattern`, ignoring
    case differences.

    :param pattern: A wildcard pattern. e.g. "*.py"
    :type pattern: str
    :param name: A filename
    :type name: str
    :rtype bool:

    """
    try:
        re_pat = _cache[(pattern, False)]
    except KeyError:
        res = _translate(pattern, case_sensitive=False)
        _cache[(pattern, False)] = re_pat =\
            re.compile(res, re.IGNORECASE)
    return re_pat.match(name) is not None


def match_any(patterns, name):
    """
    Test if a name matches at least one of a list of patterns.

    :param patterns: A list of wildcard pattern. e.g. ["*.py", "*.pyc"]
    :type pattern: list
    :param name: A filename.
    :type name: str
    :rtype bool:

    """
    if not patterns:
        return True
    return any(match(pattern, name) for pattern in patterns)


def imatch_any(patterns, name):
    """
    Test if a name matches at least one of a list of patterns, ignoring
    case differences.

    :param patterns: A list of wildcard pattern. e.g. ["*.py", "*.pyc"]
    :type pattern: list
    :param name: A filename.
    :type name: str
    :rtype bool:

    """
    if not patterns:
        return True
    return any(imatch(pattern, name) for pattern in patterns)


def get_matcher(patterns, case_sensitive):
    """
    Get a callable that checks a list of names matches the given
    wildcard patterns.

    :param patterns: A list of wildcard pattern. e.g. ["*.py", "*.pyc"]
    :type pattern: list
    :param case_sensitive: If True, then the callable will be case
        sensitive, otherwise it will be case insensitive.
    :type case_sensitive: bool
    :rtype callable:


    """
    if not patterns or patterns == '*':
        return lambda name: True
    if case_sensitive:
        return partial(match_any, patterns)
    else:
        return partial(imatch_any, patterns)


def _translate(pattern, case_sensitive=True):
    """Translate a shell PATTERN to a regular expression.

    There is no way to quote meta-characters.

    """
    if not case_sensitive:
        pattern = pattern.lower()
    i, n = 0, len(pattern)
    res = ''
    while i < n:
        c = pattern[i]
        i = i + 1
        if c == '*':
            res = res + '.*'
        elif c == '?':
            res = res + '.'
        elif c == '[':
            j = i
            if j < n and pattern[j] == '!':
                j = j + 1
            if j < n and pattern[j] == ']':
                j = j + 1
            while j < n and pattern[j] != ']':
                j = j + 1
            if j >= n:
                res = res + '\\['
            else:
                stuff = pattern[i:j].replace('\\', '\\\\')
                i = j + 1
                if stuff[0] == '!':
                    stuff = '^' + stuff[1:]
                elif stuff[0] == '^':
                    stuff = '\\' + stuff
                res = '%s[%s]' % (res, stuff)
        else:
            res = res + re.escape(c)
    return res + '\Z(?ms)'
