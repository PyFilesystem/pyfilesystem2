from __future__ import unicode_literals

from functools import partial

from ..path import join


class Patch(object):
    """Applies a individual patch."""

    def apply(self, context):
        """Apply the patch."""
        raise NotImplementedError

    def revert(self, context):
        """Restore to previous state."""
        raise NotImplementedError


class ModulePatch(Patch):
    module = None
    attrib = None
    patch_method = None

    def __init__(self):
        assert self.module is not None, "module must be a classvar"
        self._restore = None

    def __repr__(self):
        return '<patch {}.{}>'.format(
            self.module.__name__,
            self.attrib
        )

    def apply(self, context):
        self._restore = getattr(self.module, self.attrib)
        patched = partial(getattr(self, (self.patch_method or self.attrib)), context)
        setattr(self.module, self.attrib, patched)

    def revert(self, context):
        setattr(self.module, self.attrib, self._restore)
        self._restore = None



class PatchContext(object):
    """
    Patches a filesystem over builtins.

    """
    def __init__(self, filesystem, patches, cwd='/', auto_close=False):
        self.filesystem = filesystem
        self.patches = patches
        self.cwd = cwd
        self.auto_close = auto_close

        self.file_handles = {}
        self._applied_patches = []

    def get_path(self, path):
        path = join(self.cwd, path)
        return path

    def __enter__(self):
        for patch in self.patches:
            patch.apply(self)
            self._applied_patches.append(patch)
        return self

    def __exit__(self, exc_type, exc_value, tb):
        pop = self._applied_patches.pop
        try:
            while self._applied_patches:
                patch = pop()
                patch.revert(self)
        finally:
            if self.auto_close:
                self.filesystem.close()
