import pkgutil
import importlib
__path__ = pkgutil.extend_path(__path__, __name__)

from ._registry import registry, Registry
from ._errors import OpenerError, ParseError, Unsupported


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

open_fs = registry.open_fs
open = registry.open
manage_fs = registry.manage_fs
parse = registry.parse

for _, modname, _ in pkgutil.iter_modules(__path__):
    if not modname.startswith('_'):
        importlib.import_module('.'.join([__name__, modname]), package=__name__)
        __all__.append(modname)
