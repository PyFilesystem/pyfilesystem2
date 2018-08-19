from __future__ import unicode_literals

from .base import Patch


class OSPatch(Patch):
    def __init__(self):
        import os
        super(OSPatch, self).__init__(os)
