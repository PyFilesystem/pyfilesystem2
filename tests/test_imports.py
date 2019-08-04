import sys
import unittest


class TestImports(unittest.TestCase):
    def test_import_path(self):
        """Test import fs also imports other symbols."""
        restore_fs = sys.modules.pop("fs")
        sys.modules.pop("fs.path")
        try:
            import fs

            fs.path
            fs.Seek
            fs.ResourceType
            fs.open_fs
        finally:
            sys.modules["fs"] = restore_fs
