import pkgutil
__path__ = pkgutil.extend_path(__path__, __name__)

from ._registry import registry, Registry
from ._errors import OpenerError, ParseError, Unsupported

open_fs = registry.open_fs
open = registry.open
