from __future__ import unicode_literals

import os

from six import PY2

from .base import original, patch_method, Patch
from .translate_errors import raise_os
from .. import errors


class PatchOS(Patch):
    def get_module(self):
        import os
        return os

    @patch_method()
    def chdir(self, path):
        if not self.is_patched:
            return original(chdir(path))
        with raise_os():
            return self._chdir(path)

    @patch_method()
    def getcwd(self):
        if not self.is_patched:
            return original(getcwd)()
        return self.os_cwd

    @patch_method()
    def listdir(self, path):
        if not self.is_patched:
            return original(listdir)(path)
        _path = self.from_cwd(path)
        with raise_os():
            dirlist = self.fs.listdir(_path)
        return dirlist