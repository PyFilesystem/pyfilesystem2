"""
fs.expose.importhook
====================

Expose an FS object to the python import machinery, via a PEP-302 loader.

This module allows you to import python modules from an arbitrary FS object,
by placing FS urls on sys.path and/or inserting objects into sys.meta_path.

The main class in this module is FSImportHook, which is a PEP-302-compliant
module finder and loader.  If you place an instance of FSImportHook on
sys.meta_path, you will be able to import modules from the exposed filesystem::

    >>> from fs.memoryfs import MemoryFS
    >>> m = MemoryFS()
    >>> m.writetext("helloworld.py", "print('hello world!')")
    >>>
    >>> import sys
    >>> from fs.expose.importhook import FSImportHook
    >>> sys.meta_path.append(FSImportHook(m))
    >>> import helloworld
    hello world!

It is also possible to install FSImportHook as an import path handler. This
allows you to place filesystem URLs on sys.path and have them automagically
opened for importing.  This example would allow modules to be imported from
an SFTP server::

    >>> from fs.expose.importhook import FSImportHook
    >>> FSImportHook.install()
    >>> sys.path.append("sftp://some.remote.machine/mypath/")

"""
import os
import sys
import imp
import types
import marshal
import importlib
from importlib.util import MAGIC_NUMBER

from typing import Sequence, Text, Tuple, Optional

from fs import open_fs
from fs.base import FS
from fs.errors import FSError


ModuleInfo = Tuple[Text, int, bool]


class FSImportHook(importlib.abc.MetaPathFinder):
    """PEP-302-compliant module finder and loader for FS objects.

    FSImportHook is a module finder and loader that takes its data from an
    arbitrary FS object.  The FS must have .py or .pyc files stored in the
    standard module structure.

    For easy use with sys.path, FSImportHook will also accept a filesystem
    URL, which is automatically opened using fs.opener.
    """

    _VALID_MODULE_TYPES = {imp.PY_SOURCE, imp.PY_COMPILED}

    def __init__(self, fs_or_url):
        # type: ([FS, Text]) -> None
        #  If given a string, try to open it as an FS url.
        #  Don't open things on the local filesystem though.
        if (isinstance(fs_or_url, str) and ":/" not in fs_or_url) and (not isinstance(fs_or_url, FS)):
            raise ImportError()

        self.fs = open_fs(fs_or_url)
        self.path = fs_or_url if isinstance(fs_or_url, str) else None
        # Cache the 'module_info' data
        self.module_info = {}

    @classmethod
    def install(cls):
        # type: () -> None
        """Install this class into the import machinery.

        This classmethod installs the custom FSImportHook class into the
        import machinery of the running process, if it is not already
        installed.
        """
        if cls in sys.path_hooks:
            return
        sys.path_hooks.append(cls)
        sys.path_importer_cache.clear()

    @classmethod
    def uninstall(cls):
        # type: () -> None
        """Uninstall this class from the import machinery.

        This classmethod uninstalls the custom FSImportHook class from the
        import machinery of the running process.
        """
        if cls not in sys.path_hooks:
            return
        sys.path_hooks.remove(cls)
        sys.path_importer_cache.clear()

    def find_module(self, fullname, path=None):
        # type: (Text, Sequence[bytes, str]) -> [FSImportHook, None]
        """Find the FS loader for the given module.

        This object is always its own loader, so this really just checks
        whether it's a valid module on the exposed filesystem.
        """
        try:
            self._get_module_info(fullname)
        except ImportError:
            return None
        else:
            return self

    def _get_module_info(self, fullname):
        # type: (Text) -> ModuleInfo
        """Get basic information about the given module.

        If the specified module exists, this method returns a tuple giving
        its filepath, file type and whether it's a package. Otherwise,
        it raise ImportError.
        """
        if fullname in self.module_info:
            return self.module_info[fullname]

        prefix = fullname.replace(".", "/")
        #  Is it a regular module?
        path, _type = self._find_module_file(prefix)
        if path is not None:
            self.module_info[fullname] = path, _type, False
            return path, _type, False
        #  Is it a package?
        prefix = os.path.join(prefix, "__init__")
        path, _type = self._find_module_file(prefix)
        if path is not None:
            self.module_info[fullname] = path, _type, True
            return path, _type, True
        #  No, it's nothing
        raise ImportError(fullname)

    def _find_module_file(self, prefix):
        # type: (Text) -> Tuple[Optional[Text], Optional[int]]
        """Find a module file from the given path prefix.

        This method iterates over the possible module suffixes, checking each
        in turn and returning the first match found.  It returns a two-tuple
        (path,type) or (None,None) if there's no module.
        """
        for suffix, mode, _type in imp.get_suffixes():
            if _type in self._VALID_MODULE_TYPES:
                path = prefix + suffix
                if self.fs.isfile(path):
                    return path, _type
        return None, None

    def load_module(self, fullname):
        # type: (Text) -> types.ModuleType
        """Load the specified module.

        This method locates the file for the specified module, loads and
        executes it and returns the created module object.
        """
        #  Reuse an existing module if present.
        try:
            return sys.modules[fullname]
        except KeyError:
            pass
        #  Try to create from source or bytecode.
        info = self._get_module_info(fullname)
        code = self.get_code(fullname, info)
        if code is None:
            raise ImportError(fullname)
        mod = types.ModuleType(fullname)
        mod.__file__ = "<loading>"
        mod.__loader__ = self
        sys.modules[fullname] = mod
        try:
            exec(code, mod.__dict__)
            mod.__file__ = self.get_filename(fullname, info)
            if self.is_package(fullname, info):
                if self.path is None:
                    mod.__path__ = []
                else:
                    mod.__path__ = [self.path]
            return mod
        except Exception:
            sys.modules.pop(fullname, None)
            raise

    def is_package(self, fullname, info=None):
        # type: (Text, Optional[ModuleInfo]) -> bool
        """Check whether the specified module is a package."""
        if info is None:
            info = self._get_module_info(fullname)
        path, _type, ispkg = info
        return ispkg

    def get_code(self, fullname, info=None):
        # type: (Text, Optional[ModuleInfo]) -> Optional[Code]
        """Get the bytecode for the specified module."""
        if info is None:
            info = self._get_module_info(fullname)
        path, _type, ispkg = info
        code = self.fs.readbytes(path)
        if _type == imp.PY_SOURCE:
            code = code.replace(b"\r\n", b"\n")
            return compile(code, path, "exec")
        elif _type == imp.PY_COMPILED:
            if code[:4] != MAGIC_NUMBER:
                return None
            return marshal.loads(code[8:])
        else:
            return None

    def get_source(self, fullname, info=None):
        # type: (Text, Optional[ModuleInfo]) -> Optional[bytes]
        """Get the sourcecode for the specified module, if present."""
        if info is None:
            info = self._get_module_info(fullname)
        path, _type, ispkg = info
        if _type != imp.PY_SOURCE:
            return None
        return self.fs.getcontents(path, 'rb').replace(b"\r\n", b"\n")

    def get_filename(self, fullname, info=None):
        # type: (Text, Optional[ModuleInfo]) -> str
        """Get the __file__ attribute for the specified module."""
        if info is None:
            info = self._get_module_info(fullname)
        path, _type, ispkg = info
        return path
