import re

from ._base import Opener
from ._utils import parse
from ._errors import OpenerError, ParseError, Unsupported


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

registry = Registry()
