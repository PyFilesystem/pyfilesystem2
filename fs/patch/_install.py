from .patch_builtins import PatchBuiltins
from .patch_os import PatchOS


installed = False

def install():
    """Install patcher."""
    global installed
    if not installed:
        PatchBuiltins().install()
        PatchOS().install()
        installed = True

