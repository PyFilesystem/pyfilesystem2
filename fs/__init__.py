"""Python filesystem abstraction layer.
"""

__import__("pkg_resources").declare_namespace(__name__)  # type: ignore

from ._version import __version__
from .enums import ResourceType, Seek
from .opener import open_fs
from ._fscompat import fsencode, fsdecode
from . import path
from . import base

__all__ = ["__version__", "ResourceType", "Seek", "open_fs", "base"]
