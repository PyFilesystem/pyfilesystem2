import pkg_resources
pkg_resources.declare_namespace(__name__)
del pkg_resources

from ._version import __version__
from .enums import ResourceType, Seek
from .opener import open_fs

__all__ = ['__version__', 'ResourceType', 'Seek', 'open_fs']
