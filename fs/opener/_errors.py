# coding: utf-8
"""
fs.opener._errors
=================

Errors raised when attempting to open a filesystem
"""

class ParseError(ValueError):
    """Raised when attempting to parse an invalid FS URL."""


class OpenerError(Exception):
    """Base class for opener related errors."""


class Unsupported(OpenerError):
    """May be raised by opener if the opener fails to open a FS."""
