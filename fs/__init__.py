"""Python filesystem abstraction layer.
"""

__import__("pkg_resources").declare_namespace(__name__)  # type: ignore

from . import path
from ._fscompat import fsdecode, fsencode
from ._version import __version__
from .enums import ResourceType, Seek
from .opener import open_fs

__all__ = ["__version__", "ResourceType", "Seek", "open_fs"]
