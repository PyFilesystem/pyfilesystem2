from __future__ import print_function
from __future__ import unicode_literals

"""
FS Paths
========

Useful functions for FS path manipulation.

This is broadly similar to the standard ``os.path`` module but works with
paths in the canonical format expected by all FS objects (that is,
separated by forward slashes and with an optional leading slash).

"""


import re

from .errors import IllegalBackReference


__all__ = [
    "abspath",
    "basename",
    "combine",
    "dirname",
    "forcedir",
    "frombase",
    "isabs",
    "isbase",
    "isdotfile",
    "isparent",
    "issamedir",
    "iswildcard",
    "iteratepath",
    "join",
    "normpath",
    "recursepath",
    "relativefrom",
    "relpath",
    "split",
    "splitext",
]

_requires_normalization = re.compile(
    r'(^|/)\.\.?($|/)|//',
    re.UNICODE
).search


def normpath(path):
    """
    Normalize a path.

    This function simplifies a path by collapsing back-references
    and removing duplicated separators.

    :param path: Path to normalize.
    :type path: str
    :returns: A valid FS path.
    :type: str

    >>> normpath("/foo//bar/frob/../baz")
    '/foo/bar/baz'

    >>> normpath("foo/../../bar")
    Traceback (most recent call last)
        ...
    IllegalBackReference: Too many backrefs in 'foo/../../bar'

    """
    if path in ('', '/'):
        return path

    # An early out if there is no need to normalize this path
    if not _requires_normalization(path):
        return path.rstrip('/')

    prefix = '/' if path.startswith('/') else ''
    components = []
    append = components.append
    special = ('..', '.', '').__contains__
    try:
        for component in path.split('/'):
            if special(component):
                if component == '..':
                    components.pop()
            else:
                append(component)
    except IndexError:
        raise IllegalBackReference('Too many backrefs in \'%s\'' % path)
    return prefix + '/'.join(components)


def iteratepath(path):
    """
    Iterate over the individual components of a path.

    >>> iteratepath('/foo/bar/baz')
    ['foo', 'bar', 'baz']

    :param path: Path to iterate over.
    :type path: str
    :returns: A list of path components.
    :rtype: list

    """
    path = relpath(normpath(path))
    if not path:
        return []
    return path.split('/')


def recursepath(path, reverse=False):
    """
    Get intermediate paths from the root to the given path.

    :param path: A PyFilesystem path
    :type path: str
    :param reverse: Reverses the order of the paths.
    :type reverse: bool
    :returns: A list of paths.
    :rtype: list

    >>> recursepath('a/b/c')
    ['/', '/a', '/a/b', '/a/b/c']

    """
    if path in ('', '/'):
        return ['/']

    path = abspath(normpath(path)) + '/'

    paths = ['/']
    find = path.find
    append = paths.append
    pos = 1
    len_path = len(path)

    while pos < len_path:
        pos = find('/', pos)
        append(path[:pos])
        pos += 1

    if reverse:
        return paths[::-1]
    return paths


def isabs(path):
    """
    Check if a path is an absolute path.

    :param path: A filesystem path.
    :type path: str
    :rtype bool:

    """
    # Somewhat trivial, but helps to make code self-documenting
    return path.startswith('/')


def abspath(path):
    """
    Convert the given path to an absolute path.

    Since FS objects have no concept of a 'current directory' this
    simply adds a leading '/' character if the path doesn't already have
    one.

    :param path: A PyFilesytem path
    :type path: str
    :returns: An absolute path
    :rtype: str

    """
    if not path.startswith('/'):
        return '/' + path
    return path


def relpath(path):
    """
    Convert the given path to a relative path.

    This is the inverse of abspath(), stripping a leading '/' from the
    path if it is present.

    :param path: Path to adjust
    :type path: str

    >>> relpath('/a/b')
    'a/b'

    """
    return path.lstrip('/')


def join(*paths):
    """
    Join any number of paths together.

    :param paths: Paths to join are given in positional arguments.

    >>> pathjoin('foo', 'bar', 'baz')
    'foo/bar/baz'

    >>> pathjoin('foo/bar', '../baz')
    'foo/baz'

    >>> pathjoin('foo/bar', '/baz')
    '/baz'

    """
    absolute = False
    relpaths = []
    for p in paths:
        if p:
            if p[0] == '/':
                del relpaths[:]
                absolute = True
            relpaths.append(p)

    path = normpath("/".join(relpaths))
    if absolute:
        path = abspath(path)
    return path


def combine(path1, path2):
    """
    Join two paths together.

    This is faster than ``pathjoin``, but only works when the second
    path is relative, and there are no back references in either path.

    >>> combine("foo/bar", "baz")
    'foo/bar/baz'

    """
    if not path1:
        return path2.lstrip()
    return "{}/{}".format(path1.rstrip('/'), path2.lstrip('/'))


def split(path):
    """
    Split a path into (head, tail) pair.

    This function splits a path into a pair (head, tail) where 'tail' is
    the last pathname component and 'head' is all preceding components.

    :param path: Path to split
    :type path: str

    >>> split("foo/bar")
    ('foo', 'bar')

    >>> split("foo/bar/baz")
    ('foo/bar', 'baz')

    >>> split("/foo/bar/baz")
    ('/foo/bar', 'baz')

    """
    if '/' not in path:
        return ('', path)
    split = path.rsplit('/', 1)
    return (split[0] or '/', split[1])


def splitext(path):
    """
    Split the extension from the path, and returns the path (up to the
    last '.' and the extension).

    :param path: A path to split

    >>> splitext('baz.txt')
    ('baz', 'txt')

    >>> splitext('foo/bar/baz.txt')
    ('foo/bar/baz', 'txt')

    """

    parent_path, pathname = split(path)
    if '.' not in pathname:
        return path, ''
    pathname, ext = pathname.rsplit('.', 1)
    path = join(parent_path, pathname)
    return path, '.' + ext


def isdotfile(path):
    """
    Detect if a path references a dot file, i.e. a resource who's name
    starts with a '.'

    :param path: Path to check.
    :type path: str

    >>> isdotfile('.baz')
    True

    >>> isdotfile('foo/bar/.baz')
    True

    >>> isdotfile('foo/bar.baz')
    False

    """
    return basename(path).startswith('.')


def dirname(path):
    """
    Return the parent directory of a path.

    This is always equivalent to the 'head' component of the value
    returned by ``split(path)``.

    :param path: A FS path

    >>> dirname('foo/bar/baz')
    'foo/bar'

    >>> dirname('/foo/bar')
    '/foo'

    >>> dirname('/foo')
    '/'

    """
    return split(path)[0]


def basename(path):
    """
    Return the basename of the resource referenced by a path.

    This is always equivalent to the 'tail' component of the value
    returned by split(path).

    :param path: A FS path
    :type path: str

    >>> basename('foo/bar/baz')
    'baz'

    >>> basename('foo/bar')
    'bar'

    >>> basename('foo/bar/')
    ''

    """
    return split(path)[1]


def issamedir(path1, path2):
    """
    Check if two paths reference a resource in the same directory.

    :param path1: A FS path.
    :type path1: str
    :param path2: A FS path.
    :type path2: str

    >>> issamedir("foo/bar/baz.txt", "foo/bar/spam.txt")
    True
    >>> issamedir("foo/bar/baz/txt", "spam/eggs/spam.txt")
    False

    """
    return dirname(normpath(path1)) == dirname(normpath(path2))


def isbase(path1, path2):
    """Check if path1 is a base of path2."""
    p1 = forcedir(abspath(path1))
    p2 = forcedir(abspath(path2))
    return p1 == p2 or p1.startswith(p2)


def isparent(path1, path2):
    """
    Check if ``path1`` is a parent directory of ``path2``.

    :param path1: An FS path
    :param path2: An FS path

    >>> isparent("foo/bar", "foo/bar/spam.txt")
    True
    >>> isparent("foo/bar/", "foo/bar")
    True
    >>> isparent("foo/barry", "foo/baz/bar")
    False
    >>> isparent("foo/bar/baz/", "foo/baz/bar")
    False

    """
    bits1 = path1.split("/")
    bits2 = path2.split("/")
    while bits1 and bits1[-1] == "":
        bits1.pop()
    if len(bits1) > len(bits2):
        return False
    for (bit1, bit2) in zip(bits1, bits2):
        if bit1 != bit2:
            return False
    return True


def forcedir(path):
    """
    Ensure the path ends with a trailing forward slash

    :param path: An FS path

    >>> forcedir("foo/bar")
    'foo/bar/'
    >>> forcedir("foo/bar/")
    'foo/bar/'

    """

    if not path.endswith('/'):
        return path + '/'
    return path


def frombase(path1, path2):
    """
    Get the final path of ``path2`` that isn't in ``path1``.

    >>> frombase('foo/bar/', 'foo/bar/baz/egg')
    'baz/egg'

    """
    if not isparent(path1, path2):
        raise ValueError("path1 must be a prefix of path2")
    return path2[len(path1):]


def relativefrom(base, path):
    """
    Return a path relative from a given base path, i.e. insert backrefs
    as appropriate to reach the path from the base.

    :param base: Path to a directory.
    :type base: str
    :param path: Path you wish to make relative.
    :type path: str

    >>> relativefrom("foo/bar", "baz/index.html")
    '../../baz/index.html'

    """
    base = list(iteratepath(base))
    path = list(iteratepath(path))

    common = 0
    for a, b in zip(base, path):
        if a != b:
            break
        common += 1

    return '/'.join(['..'] * (len(base) - common) + path[common:])


_wild_chars = frozenset('*?[]!{}')


def iswildcard(path):
    """
    Check if a path ends with a wildcard.

    >>> is_wildcard('foo/bar/baz.*')
    True
    >>> is_wildcard('foo/bar')
    False

    """
    assert path is not None
    return not _wild_chars.isdisjoint(path)
