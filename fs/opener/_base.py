# coding: utf-8
"""
fs.opener._base
===============

Defines the Opener abstract base class.
"""

import six
import abc


@six.add_metaclass(abc.ABCMeta)
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

    @abc.abstractmethod
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
