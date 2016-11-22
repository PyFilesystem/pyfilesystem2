from __future__ import unicode_literals

import unittest

import six

from fs.appfs import UserDataFS


class TestAppFS(unittest.TestCase):
    """Test Application FS."""

    def test_user_data(self):
        """Test UserDataFS."""
        user_data_fs = UserDataFS('fstest', 'willmcgugan', '1.0')
        if six.PY2:
            self.assertEqual(
                repr(user_data_fs),
                "UserDataFS(u'fstest', author=u'willmcgugan', version=u'1.0')"
            )
        else:
            self.assertEqual(
                repr(user_data_fs),
                "UserDataFS('fstest', author='willmcgugan', version='1.0')"
            )
        self.assertEqual(
            str(user_data_fs),
            "<userdatafs 'fstest'>"
        )
