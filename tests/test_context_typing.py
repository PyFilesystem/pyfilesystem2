"""Check preservation of concrete filesystem types in context managers."""
from __future__ import unicode_literals

import unittest

try:
    from mypy import api as mypy_api
except ImportError:
    mypy_api = None


class TestContextTyping(unittest.TestCase):
    @unittest.skipIf(mypy_api is None, "mypy is not installed")
    def test_context_manager_preserves_subclass_type(self):
        source = """
from fs.memoryfs import MemoryFS
from fs.osfs import OSFS
from fs.tempfs import TempFS

def accepts_temp(fs):
    # type: (TempFS) -> None
    pass

with TempFS() as temp:
    accepts_temp(temp)

with OSFS(".") as osfs:
    concrete = osfs  # type: OSFS

class CustomFS(MemoryFS):
    def custom_method(self):
        # type: () -> int
        return 1

with CustomFS() as custom:
    custom.custom_method()
"""
        output, error, status = mypy_api.run(
            ["--follow-imports=silent", "--no-incremental", "-c", source]
        )
        self.assertEqual(status, 0, output + error)
