import sys
import unittest


class TestImports(unittest.TestCase):
    def test_import_path(self):
        """Test import fs also imports other symbols."""
        sys.modules.pop("fs")
        import fs

        fs.path
        fs.Seek
        fs.ResourceType
        fs.open_fs
