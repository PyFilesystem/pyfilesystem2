from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

from contextlib import contextmanager
import os
import re

from collections import namedtuple


ParseResult = namedtuple(
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


@contextmanager
def manage_fs(fs_url, create=False, writeable=True, cwd='.'):
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
    from .base import FS
    if isinstance(fs_url, FS):
        yield fs_url
    else:
        _fs = open_fs(
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


class ParseError(ValueError):
    """Raised when attempting to parse an invalid FS URL."""


class OpenerError(Exception):
    """Base class for opener related errors."""


class Unsupported(OpenerError):
    """May be raised by opener if the opener fails to open a FS."""


def parse(fs_url):
    """
    Parse a Filesystem URL and return a :class:`ParseResult`, or raise
    :class:`ParseError` (subclass of ValueError) if the FS URL is
    not value.

    :param fs_url: A filesystem URL
    :type fs_url: str
    :rtype: :class:`ParseResult`

    """
    match = _RE_FS_URL.match(fs_url)
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
    return ParseResult(
        fs_name,
        username,
        password,
        url,
        path
    )




class Opener(object):
    """
    The opener base class.

    An opener is responsible for opening a filesystems from one or more
    protocols. A list of supported protocols is supplied in a class
    attribute called `protocols`.

    Openers should be registered with a :class:`~fs.opener.Registry`
    object, which picks an appropriate opener object for a given FS URL.

    """

    protocols = []

    def __repr__(self):
        return "<opener {!r}>".format(self.protocols)

    def open_fs(self, fs_url, parse_result, writeable, create, cwd):
        """
        Open a filesystem object from a FS URL.

        :param str fs_url: A filesystem URL
        :param parse_result: A parsed filesystem URL.
        :type parse_result: :class:`ParseResult`
        :param bool writeable: True if the filesystem must be writeable.
        :param bool create: True if the filesystem should be created if
            it does not exist.
        :param str cwd: The current working directory (generally only
            relevant for OS filesystems).
        :returns: :class:`~fs.base.FS` object

        """


class Registry(object):
    """
    A registry for `Opener` instances.

    """

    def __init__(self, default_opener='osfs'):
        """
        Create a registry object.

        :param default_opener: The protocol to use, if one is not
            supplied. The default is to use 'osfs', so that the FS URL
            is treated as a system path if no protocol is given.

        """
        self.default_opener = default_opener
        self.protocols = {}

    def install(self, opener):
        """
        Install an opener.

        :param opener: An :class:`Opener` instance, or a callable
            that returns an opener instance.

        May be used as a class decorator. For example::

            registry = Registry()

            @registry.install
            class ArchiveOpener(Opener):
                protocols = ['zip', 'tar']

        """
        if not isinstance(opener, Opener):
            opener = opener()
        assert opener.protocols, "must list one or more protocols"
        for protocol in opener.protocols:
            self.protocols[protocol] = opener

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

        parse_result = parse(fs_url)
        protocol = parse_result.protocol
        open_path = parse_result.path

        opener = self.protocols.get(protocol, None)

        if not opener:
            raise Unsupported(
                "protocol '{}' is not supported".format(protocol)
            )

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
        from .base import FS
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


registry = Registry()
open_fs = registry.open_fs
open = registry.open


@registry.install
class OSFSOpener(Opener):
    protocols = ['file', 'osfs']

    def open_fs(self, fs_url, parse_result, writeable, create, cwd):
        from .osfs import OSFS
        _path = os.path.abspath(os.path.join(cwd, parse_result.resource))
        path = os.path.normpath(_path)
        osfs = OSFS(path, create=create)
        return osfs


@registry.install
class TempOpener(Opener):
    protocols = ['temp']

    def open_fs(self, fs_url, parse_result, writeable, create, cwd):
        from .tempfs import TempFS
        temp_fs = TempFS(identifier=parse_result.resource)
        return temp_fs


@registry.install
class MemOpener(Opener):
    protocols = ['mem']

    def open_fs(self, fs_url, parse_result, writeable, create, cwd):
        from .memoryfs import MemoryFS
        mem_fs = MemoryFS()
        return mem_fs


@registry.install
class ZipOpener(Opener):
    protocols = ['zip']

    def open_fs(self, fs_url, parse_result, writeable, create, cwd):
        from .zipfs import ZipFS
        zip_fs = ZipFS(
            parse_result.resource,
            write=create
        )
        return zip_fs

@registry.install
class TarOpener(Opener):
    protocols = ['tar']

    def open_fs(self, fs_url, parse_result, writeable, create, cwd):
        from .tarfs import TarFS
        tar_fs = TarFS(
            parse_result.resource,
            write=create
        )
        return tar_fs


@registry.install
class FTPOpener(Opener):
    protocols = ['ftp']

    def open_fs(self, fs_url, parse_result, writeable, create, cwd):
        from .ftpfs import FTPFS
        ftp_host, _, dir_path = parse_result.resource.partition('/')
        ftp_host, _, ftp_port = ftp_host.partition(':')
        ftp_port = int(ftp_port) if ftp_port.isdigit() else 21
        ftp_fs = FTPFS(
            ftp_host,
            port=ftp_port,
            user=parse_result.username,
            passwd=parse_result.password,
        )
        ftp_fs = (
            ftp_fs.opendir(dir_path)
            if dir_path else
            ftp_fs
        )
        return ftp_fs
