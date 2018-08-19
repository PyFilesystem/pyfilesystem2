from __future__ import unicode_literals

import logging
from types import TracebackType
from typing import List, Optional, Type

from ..base import FS


log = logging.getLogger("fs.patch")


class NotPatched(Exception):
    pass


def original(method):
    _patch = method._fspatch
    original = _patch['original']
    return original


def patch_method():
    def deco(f):
        f._fspatch = {}
        return f
    return deco


class Patch(object):

    def get_module(self):
        raise NotImplementedError()

    @property
    def fs(self):
        if PatchContext.stack:
            return fs[-1]
        else:
            raise NotPatched()

    def install(self):
        for method_name in dir(self):
            method = getattr(self, method_name)
            _patch = getattr(method, "_fspatch", None)
            if _patch is None:
                continue
            original = getattr(self.module, method_name)
            _patch["original"] = original
            setattr(self.module, method_name, method)


class PatchContext(object):
    stack = []  # type: List[FS]

    def __init__(self, fs_obj, auto_close=False):
        self.fs_obj = fs_obj
        self.auto_close = auto_close

    def __enter__(self):
        self.stack.append(self.fs_obj)
        log.debug('%r patched', self.fs_obj)
        return self

    def __exit__(
        self,
        exc_type,  # type: Optional[Type[BaseException]]
        exc_value,  # type: Optional[BaseException]
        traceback,  # type: Optional[TracebackType]
    ):
        fs_obj = self.stack.pop()
        log.debug('%r un-patched', fs_obj)
        if self.auto_close:
            fs_obj.close()
