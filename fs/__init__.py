"""Python filesystem abstraction layer.
"""

__path__ = __import__("pkgutil").extend_path(__path__, __name__)

from . import path
from ._fscompat import fsdecode, fsencode
from ._version import __version__
from .enums import ResourceType, Seek
from .opener import open_fs

__all__ = ["__version__", "ResourceType", "Seek", "open_fs"]
