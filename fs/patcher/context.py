from __future__ import unicode_literals

from functools import partial

import six

from .stack import context_stack
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
    method_name = None

    def __init__(self):
        assert self.module is not None, "module must be a classvar"
        self._restore = None
        self.context = None

    def __repr__(self):
        return '<{} {}.{}>'.format(
            self.__class__.__name__,
            self.module.__name__,
            self.attrib
        )

    @property
    def replace_method(self):
        return getattr(self, (self.method_name or self.attrib))

    def apply(self, context):
        self.context = context
        self._restore = getattr(self.module, self.attrib)
        setattr(self.module, self.attrib, self.replace_method)

    def revert(self, context):
        setattr(self.module, self.attrib, self._restore)
        self._restore = None


class CodePatch(ModulePatch):
    module = None
    attrib = None

    def apply(self, context):
        self.context = context
        original_method = getattr(self.module, self.attrib)

        self._restore = getattr(
            original_method,
            '__code__'
        )
        patch = getattr(self, (self.method_name or self.attrib))
        replace_code = patch.__code__
        setattr(
            original_method,
            '__code__',
            replace_code
        )

    def revert(self, context):
        setattr(
            getattr(self.module, self.attrib),
            '__code__',
            self._restore
        )
        self._restore = None
        self.context = None


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
        context_stack.append(self)
        for patch in self.patches:
            patch.apply(self)
            self._applied_patches.append(patch)
        return self

    def __exit__(self, exc_type, exc_value, tb):
        context_stack.pop()
        pop = self._applied_patches.pop
        try:
            while self._applied_patches:
                patch = pop()
                patch.revert(self)
        finally:
            if self.auto_close:
                self.filesystem.close()
