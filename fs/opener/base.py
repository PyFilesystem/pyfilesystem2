# coding: utf-8
"""`Opener` abstract base class.
"""

import six
import abc


@six.add_metaclass(abc.ABCMeta)
class Opener(object):
    """The base class for filesystem openers.

    An opener is responsible for opening a filesystem for a given
    protocol.

    """

    protocols = []

    def __repr__(self):
        return "<opener {!r}>".format(self.protocols)

    @abc.abstractmethod
    def open_fs(self, fs_url, parse_result, writeable, create, cwd):
        """Open a filesystem object from a FS URL.

        Arguments:
            fs_url (str): A filesystem URL.
            parse_result (~fs.opener.parse.ParseResult): A parsed
                filesystem URL.
            writeable (bool): `True` if the filesystem must be writable.
            create (bool): `True` if the filesystem should be created
                if it does not exist.
            cwd (str): The current working directory (generally only
                relevant for OS filesystems).

        Raises:
            fs.opener.errors.OpenerError: If a filesystem could not
                be opened for any reason.

        Returns:
            `~fs.base.FS`: A filesystem instance.

        """
