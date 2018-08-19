from __future__ import unicode_literals

from .base import Patch


class OSPatch(Patch):
    def get_module(self):
        import os
        return os
