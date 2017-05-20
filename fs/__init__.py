from pkgutil import extend_path
__path__ = extend_path(__path__, __name__)

from ._version import __version__
from .enums import ResourceType, Seek
from .opener import open_fs
