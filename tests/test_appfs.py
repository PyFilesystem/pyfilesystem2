from __future__ import unicode_literals

import pytest
import six

from fs import appfs


@pytest.fixture
def fs(mock_appdir_directories):
    """Create a UserDataFS but strictly using a temporary directory."""
    return appfs.UserDataFS("fstest", "willmcgugan", "1.0")


@pytest.mark.skipif(six.PY2, reason="Test requires Python 3 repr")
def test_user_data_repr_py3(fs):
    assert repr(fs) == "UserDataFS('fstest', author='willmcgugan', version='1.0')"
    assert str(fs) == "<userdatafs 'fstest'>"


@pytest.mark.skipif(not six.PY2, reason="Test requires Python 2 repr")
def test_user_data_repr_py2(fs):
    assert repr(fs) == "UserDataFS(u'fstest', author=u'willmcgugan', version=u'1.0')"
    assert str(fs) == "<userdatafs 'fstest'>"
