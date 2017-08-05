# coding: utf-8
"""
fs.opener.errors
================

Errors raised when attempting to open a filesystem.

"""

class ParseError(ValueError):
    """Raised when attempting to parse an invalid FS URL."""


class OpenerError(Exception):
    """Base class for opener related errors."""


class UnsupportedProtocol(OpenerError):
    """May be raised if no opener could be found for a given
    protocol."""


class EntryPointError(OpenerError):
    """Raised by the registry when an entry point cannot be loaded."""
