from __future__ import unicode_literals

import errno
import unittest

from fs.error_tools import convert_os_errors
from fs import errors as fserrors


class TestErrorTools(unittest.TestCase):

    def assert_convert_os_errors(self):

        with self.assertRaises(fserrors.ResourceNotFound):
            with convert_os_errors('foo', 'test'):
                raise OSError(errno.ENOENT)
