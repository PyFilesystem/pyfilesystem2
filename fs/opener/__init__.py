# coding: utf-8
"""
fs.opener
========

Imported at the same time as PyFilesystem2, contains
various objects and functions to open and manage FS.
"""

import importlib

# Declares fs.opener as a namespace package
import pkgutil
__path__ = pkgutil.extend_path(__path__, __name__)

# Import objects into fs.opener namespace
from ._registry import registry, Registry
from ._errors import OpenerError, ParseError, Unsupported

# Create a partial __all__ with imports and aliases
__all__ = [
    "registry",
    "Registry",
    "OpenerError",
    "ParseError",
    "Unsupported",
    'open_fs',
    'open',
    'manage_fs',
    'parse',
]

# Alias functions defined as Registry methods
open_fs = registry.open_fs
open = registry.open
manage_fs = registry.manage_fs
parse = registry.parse

# Import any file in the opener directory not prefixed by an underscore
# and add its name to the __all__ list when successful
for _, modname, _ in pkgutil.iter_modules(__path__):
    if not modname.startswith('_'):
        importlib.import_module('.'.join([__name__, modname]), package=__name__)
        __all__.append(modname)
