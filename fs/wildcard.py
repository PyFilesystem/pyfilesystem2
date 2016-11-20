"""Match wildcard filenames."""
# Adapted from https://hg.python.org/cpython/file/2.7/Lib/fnmatch.py

from __future__ import unicode_literals

import re
from functools import partial

from .lrucache import LRUCache

_MAXCACHE = 1000
_PATTERN_CACHE = LRUCache(_MAXCACHE)


def match(pattern, name):
    """
    Test whether ``name`` matches ``pattern``.

    :param str pattern: A wildcard pattern. e.g. ``"*.py"``
    :param str name: A filename
    :rtype: bool

    """
    try:
        re_pat = _PATTERN_CACHE[(pattern, True)]
    except KeyError:
        res = _translate(pattern)
        _PATTERN_CACHE[(pattern, True)] = re_pat = re.compile(res)
    return re_pat.match(name) is not None


def imatch(pattern, name):
    """
    Test whether ``name`` matches ``pattern``, ignoring
    case differences.

    :param str pattern: A wildcard pattern. e.g. ``"*.py"``
    :param str name: A filename
    :rtype: bool

    """
    try:
        re_pat = _PATTERN_CACHE[(pattern, False)]
    except KeyError:
        res = _translate(pattern, case_sensitive=False)
        _PATTERN_CACHE[(pattern, False)] = re_pat =\
            re.compile(res, re.IGNORECASE)
    return re_pat.match(name) is not None


def match_any(patterns, name):
    """
    Test if a name matches at least one of a list of patterns. Will
    return ``True`` if ``patterns`` is an empty list.

    :param list patterns: A list of wildcard pattern. e.g. ``["*.py",
        "*.pyc"]``
    :param str name: A filename.
    :rtype: bool

    """
    if not patterns:
        return True
    return any(match(pattern, name) for pattern in patterns)


def imatch_any(patterns, name):
    """
    Test if a name matches at least one of a list of patterns, ignoring
    case differences. Will return ``True`` if ``patterns`` is an empty
    list.

    :param list patterns: A list of wildcard pattern. e.g. ``["*.py",
        "*.pyc"]``
    :param str name: A filename.
    :rtype: bool

    """
    if not patterns:
        return True
    return any(imatch(pattern, name) for pattern in patterns)


def get_matcher(patterns, case_sensitive):
    """
    Get a callable that checks a list of names matches the given
    wildcard patterns.

    :param list patterns: A list of wildcard pattern. e.g. ``["*.py",
        "*.pyc"]``
    :param bool case_sensitive: If True, then the callable will be case
        sensitive, otherwise it will be case insensitive.
    :rtype: callable

    Here's an example::

    >>> import wildcard
    >>> is_python = wildcard.get_macher(['*.py'])
    >>> is_python('__init__.py')
    >>> True
    >>> is_python('foo.txt')
    >>> False

    """
    if not patterns:
        return lambda name: True
    if case_sensitive:
        return partial(match_any, patterns)
    else:
        return partial(imatch_any, patterns)


def _translate(pattern, case_sensitive=True):
    """
    Translate a shell PATTERN to a regular expression.

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
