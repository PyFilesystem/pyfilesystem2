"""Python filesystem abstraction layer.
"""

from ._version import __version__
from .enums import ResourceType, Seek
from .opener import open_fs
from ._fscompat import fsencode, fsdecode
from . import path

__all__ = ["__version__", "ResourceType", "Seek", "open_fs"]
