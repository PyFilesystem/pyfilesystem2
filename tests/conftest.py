import pytest

try:
    from unittest import mock
except ImportError:
    import mock


@pytest.fixture
@mock.patch("appdirs.user_data_dir", autospec=True, spec_set=True)
@mock.patch("appdirs.site_data_dir", autospec=True, spec_set=True)
@mock.patch("appdirs.user_config_dir", autospec=True, spec_set=True)
@mock.patch("appdirs.site_config_dir", autospec=True, spec_set=True)
@mock.patch("appdirs.user_cache_dir", autospec=True, spec_set=True)
@mock.patch("appdirs.user_state_dir", autospec=True, spec_set=True)
@mock.patch("appdirs.user_log_dir", autospec=True, spec_set=True)
def mock_appdir_directories(
    user_log_dir_mock,
    user_state_dir_mock,
    user_cache_dir_mock,
    site_config_dir_mock,
    user_config_dir_mock,
    site_data_dir_mock,
    user_data_dir_mock,
    tmpdir
):
    """Mock out every single AppDir directory so tests can't access real ones."""
    user_log_dir_mock.return_value = str(tmpdir.join("user_log").mkdir())
    user_state_dir_mock.return_value = str(tmpdir.join("user_state").mkdir())
    user_cache_dir_mock.return_value = str(tmpdir.join("user_cache").mkdir())
    site_config_dir_mock.return_value = str(tmpdir.join("site_config").mkdir())
    user_config_dir_mock.return_value = str(tmpdir.join("user_config").mkdir())
    site_data_dir_mock.return_value = str(tmpdir.join("site_data").mkdir())
    user_data_dir_mock.return_value = str(tmpdir.join("user_data").mkdir())
