from __future__ import unicode_literals

import logging
import os
from types import TracebackType
from typing import List, Optional, Type

from ..base import FS
from ..path import join


log = logging.getLogger("fs.patch")


class NotPatched(Exception):
    pass


def original(method):
    _patch = method._fspatch
    original = _patch['original']
    return original


class Patch(object):

    stack = []  # type: List[PatchContext]

    def get_module(self):
        raise NotImplementedError()

    @classmethod
    def method(cls):
        def deco(f):
            f._fspatch = {}
            return f
        return deco

    @classmethod
    def push(self, context):
        self.stack.append(context)

    @classmethod
    def pop(self):
        return self.stack.pop()

    @property
    def is_patched(self):
        return bool(self.stack)

    @property
    def context(self):
        if self.stack:
            return self.stack[-1]
        else:
            raise NotPatched()

    @property
    def fs(self):
        if self.stack:
            return self.stack[-1].fs_obj
        else:
            raise NotPatched()

    @property
    def cwd(self):
        if self.stack:
            return self.stack[-1].cwd
        else:
            raise NotPatched()

    @property
    def os_cwd(self):
        if not self.stack:
            raise NotPatched()
        return self.to_syspath(self.stack[-1].cwd)

    def from_cwd(self, path):
        _path = self.to_fspath(path)
        abs_path = join(self.cwd, _path)
        return abs_path

    def to_fspath(self, syspath):
        return syspath.replace(os.sep, '/')

    def to_syspath(self, path):
        return path.replace('/', os.sep)

    def _chdir(self, path):
        context = self.context
        new_cwd = os.path.join(context.cwd, path)
        context.cwd = new_cwd

    def make_syspath(path):

        os.path.join(context.cwd, path)

    def install(self):
        module = self.get_module()

        for method_name, unbound_method in self.__class__.__dict__.items():
            _patch = getattr(unbound_method, "_fspatch", None)
            if _patch is None:
                continue
            method = getattr(self, method_name)
            _patch["original"] = method

            setattr(module, method_name, method)


class PatchContext(object):

    def __init__(self, fs_obj, auto_close=False):
        self.fs_obj = fs_obj
        self.auto_close = auto_close
        self.cwd = "/"

    def __repr__(self):
        return "<patch {!r} auto_close={!r} cwd={!r}>".format(self.fs_obj, self.auto_close, self.cwd)

    def __enter__(self):
        Patch.push(self)
        log.debug('%r patched', self)
        return self

    def __exit__(
        self,
        exc_type,  # type: Optional[Type[BaseException]]
        exc_value,  # type: Optional[BaseException]
        traceback,  # type: Optional[TracebackType]
    ):
        context = Patch.pop()
        log.debug('%r un-patched', context)
        if self.auto_close:
            context.fs_obj.close()
