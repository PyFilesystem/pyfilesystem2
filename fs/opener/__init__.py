# coding: utf-8
"""
fs.opener
========

Imported at the same time as PyFilesystem2, contains
various objects and functions to open and manage FS.
"""

# Declare fs.opener as a namespace package
__import__('pkg_resources').declare_namespace(__name__)

# Import objects into fs.opener namespace
from .base import Opener
from .registry import registry

# Alias functions defined as Registry methods
open_fs = registry.open_fs
open = registry.open
manage_fs = registry.manage_fs
parse = registry.parse

# __all__ with aliases and classes
__all__ = [
    "registry",
    "Opener",
    'open_fs',
    'open',
    'manage_fs',
    'parse',
]
