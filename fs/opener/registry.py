# coding: utf-8
"""
fs.opener._registry
===================

Defines the Registry, which maps protocols and FS URLs to their
respective Opener.
"""

import re
import six
import contextlib
import collections
import pkg_resources

from .base import Opener
from .errors import ParseError, Unsupported, EntryPointError


class Registry(object):
    """
    A registry for `Opener` instances.

    """

    ParseResult = collections.namedtuple(
        'ParseResult',
        [
            'protocol',
            'username',
            'password',
            'resource',
            'path'
        ]
    )

    _RE_FS_URL = re.compile(r'''
    ^
    (.*?)
    :\/\/

    (?:
    (?:(.*?)@(.*?))
    |(.*?)
    )

    (?:
    !(.*?)$
    )*$
    ''', re.VERBOSE)

    @classmethod
    def parse(cls, fs_url):
        """
        Parse a Filesystem URL and return a :class:`ParseResult`, or raise
        :class:`ParseError` (subclass of ValueError) if the FS URL is
        not value.

        :param fs_url: A filesystem URL
        :type fs_url: str
        :rtype: :class:`ParseResult`

        """
        match = cls._RE_FS_URL.match(fs_url)
        if match is None:
            raise ParseError('{!r} is not a fs2 url'.format(fs_url))

        fs_name, credentials, url1, url2, path = match.groups()
        if credentials:
            username, _, password = credentials.partition(':')
            url = url1
        else:
            username = None
            password = None
            url = url2
        return cls.ParseResult(
            fs_name,
            username,
            password,
            url,
            path
        )

    @property
    def protocols(self):
        return [entry_point.name for entry_point \
                in pkg_resources.iter_entry_points('fs.opener')]

    def __init__(self, default_opener='osfs'):
        """
        Create a registry object.

        :param default_opener: The protocol to use, if one is not
            supplied. The default is to use 'osfs', so that the FS URL
            is treated as a system path if no protocol is given.

        """
        self.default_opener = default_opener

    def get_opener(self, protocol):
        """Get the opener class associated to a given protocol.

        :param str protocol: A filesystem URL protocol
        :rtype: ``Opener``
        :raises Unsupported: If no opener could be found
        :raises EntryPointLoadingError: If the returned entry point is not
            an ``Opener`` subclass or could not be loaded successfully.
        """
        entry_point = next(
            pkg_resources.iter_entry_points('fs.opener', protocol), None)

        if entry_point is None:
            raise Unsupported(
                "protocol '{}' is not supported".format(protocol))

        try:
            opener = entry_point.load()

        except Exception as exception:
            six.raise_from(
                EntryPointError('could not load entry point'),
                exception)

        else:
            if not issubclass(opener, Opener):
                raise EntryPointError('entry point did not return an opener')

        try:
            opener_instance = opener()
        except Exception as exception:
            six.raise_from(
                EntryPointError('could not instantiate opener'),
                exception)

        return opener_instance

    def open(self,
             fs_url,
             writeable=True,
             create=False,
             cwd=".",
             default_protocol='osfs'):
        """
        Open a filesystem from a FS URL. Returns a tuple of a filesystem
        object and a path. If there is no path in the FS URL, the path
        value will be ``None``.

        :param str fs_url: A filesystem URL
        :param bool writeable: True if the filesystem must be writeable.
        :param bool create: True if the filesystem should be created if
            it does not exist.
        :param cwd: The current working directory.
        :type cwd: str or None
        :rtype: Tuple of ``(<filesystem>, <path from url>)``

        """

        if '://' not in fs_url:
            # URL may just be a path
            fs_url = "{}://{}".format(default_protocol, fs_url)

        parse_result = self.parse(fs_url)
        protocol = parse_result.protocol
        open_path = parse_result.path

        opener = self.get_opener(protocol)

        open_fs = opener.open_fs(
            fs_url,
            parse_result,
            writeable,
            create,
            cwd
        )
        return open_fs, open_path

    def open_fs(self,
                fs_url,
                writeable=True,
                create=False,
                cwd=".",
                default_protocol='osfs'):
        """
        Open a filesystem object from a FS URL (ignoring the path
        component).

        :param str fs_url: A filesystem URL
        :param parse_result: A parsed filesystem URL.
        :type parse_result: :class:`ParseResult`
        :param bool writeable: True if the filesystem must be writeable.
        :param bool create: True if the filesystem should be created if
            it does not exist.
        :param str cwd: The current working directory (generally only
            relevant for OS filesystems).
        :param str default_protocol: The protocol to use if one is not
            supplied in the FS URL (defaults to ``"osfs"``).
        :returns: :class:`~fs.base.FS` object

        """
        from ..base import FS
        if isinstance(fs_url, FS):
            _fs = fs_url
        else:
            _fs, _path = self.open(
                fs_url,
                writeable=writeable,
                create=create,
                cwd=cwd,
                default_protocol=default_protocol
            )
        return _fs

    @contextlib.contextmanager
    def manage_fs(self, fs_url, create=False, writeable=True, cwd='.'):
        '''
        A context manager opens / closes a filesystem.

        :param fs_url: A FS instance or a FS URL.
        :type fs_url: str or FS
        :param bool create: If ``True``, then create the filesytem if it
            doesn't already exist.
        :param bool writeable: If ``True``, then the filesystem should be
            writeable.
        :param str cwd: The current working directory, if opening a
            :class:`~fs.osfs.OSFS`.

        Sometimes it is convenient to be able to pass either a FS object
        *or* an FS URL to a function. This context manager handles the
        required logic for that.

        Here's an example::

            def print_ls(list_fs):
                """List a directory."""
                with manage_fs(list_fs) as fs:
                    print(" ".join(fs.listdir()))

        This function may be used in two ways. You may either pass either a
        ``str``, as follows::

            print_list('zip://projects.zip')

        Or, an FS instance::

            from fs.osfs import OSFS
            projects_fs = OSFS('~/')
            print_list(projects_fs)

        '''
        from ..base import FS
        if isinstance(fs_url, FS):
            yield fs_url
        else:
            _fs = self.open_fs(
                fs_url,
                create=create,
                writeable=writeable,
                cwd=cwd
            )
            try:
                yield _fs
            except:
                raise
            finally:
                _fs.close()



registry = Registry()
