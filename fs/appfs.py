"""Manage filesystems in platform-specific application directories.

These classes abstract away the different requirements for user data
across platforms, which vary in their conventions. They are all
subclasses of `~fs.osfs.OSFS`.

"""
# Thanks to authors of https://pypi.python.org/pypi/appdirs

# see http://technet.microsoft.com/en-us/library/cc766489(WS.10).aspx

from .osfs import OSFS
from ._repr import make_repr
from appdirs import AppDirs

__all__ = ['UserDataFS',
           'UserConfigFS',
           'SiteDataFS',
           'SiteConfigFS',
           'UserCacheFS',
           'UserLogFS']


class _AppFS(OSFS):
    """Abstract base class for an app FS.
    """

    app_dir = None

    def __init__(self,
                 appname,
                 author=None,
                 version=None,
                 roaming=False,
                 create=True):
        self.app_dirs = AppDirs(appname, author, version, roaming)
        self.create = create
        super(_AppFS, self).__init__(
            getattr(self.app_dirs, self.app_dir),
            create=create
        )

    def __repr__(self):
        return make_repr(
            self.__class__.__name__,
            self.app_dirs.appname,
            author=(self.app_dirs.appauthor, None),
            version=(self.app_dirs.version, None),
            roaming=(self.app_dirs.roaming, False),
            create=(self.create, True)
        )

    def __str__(self):
        return "<{} '{}'>".format(
            self.__class__.__name__.lower(),
            self.app_dirs.appname
        )

class UserDataFS(_AppFS):
    """A filesystem for per-user application data.

    May also be opened with
    ``open_fs('userdata://appname:author:version')``.

    Arguments:
        appname (str): The name of the application.
        author (str): The name of the author (used on Windows).
        version (str): Optional version string, if a unique location
            per version of the application is required.
        roaming (bool): If `True`, use a *roaming* profile on
            Windows.
        create (bool): If `True` (the default) the directory
            will be created if it does not exist.

    """

    app_dir = 'user_data_dir'


class UserConfigFS(_AppFS):
    """A filesystem for per-user config data.

    May also be opened with
    ``open_fs('userconf://appname:author:version')``.

    Arguments:
        appname (str): The name of the application.
        author (str): The name of the author (used on Windows).
        version (str): Optional version string, if a unique location
            per version of the application is required.
        roaming (bool): If `True`, use a *roaming* profile on
            Windows.
        create (bool): If `True` (the default) the directory
            will be created if it does not exist.

    """

    app_dir = 'user_config_dir'


class UserCacheFS(_AppFS):
    """A filesystem for per-user application cache data.

    May also be opened with
    ``open_fs('usercache://appname:author:version')``.

    Arguments:
        appname (str): The name of the application.
        author (str): The name of the author (used on Windows).
        version (str): Optional version string, if a unique location
            per version of the application is required.
        roaming (bool): If `True`, use a *roaming* profile on
            Windows.
        create (bool): If `True` (the default) the directory
            will be created if it does not exist.

    """

    app_dir = 'user_cache_dir'


class SiteDataFS(_AppFS):
    """A filesystem for application site data.

    May also be opened with
    ``open_fs('sitedata://appname:author:version')``.

    Arguments:
        appname (str): The name of the application.
        author (str): The name of the author (used on Windows).
        version (str): Optional version string, if a unique location
            per version of the application is required.
        roaming (bool): If `True`, use a *roaming* profile on
            Windows.
        create (bool): If `True` (the default) the directory
            will be created if it does not exist.

    """

    app_dir = 'site_data_dir'


class SiteConfigFS(_AppFS):
    """A filesystem for application config data.

    May also be opened with
    ``open_fs('siteconf://appname:author:version')``.

    Arguments:
        appname (str): The name of the application.
        author (str): The name of the author (used on Windows).
        version (str): Optional version string, if a unique location
            per version of the application is required.
        roaming (bool): If `True`, use a *roaming* profile on
            Windows.
        create (bool): If `True` (the default) the directory
            will be created if it does not exist.

    """

    app_dir = 'site_config_dir'


class UserLogFS(_AppFS):
    """A filesystem for per-user application log data.

    May also be opened with
    ``open_fs('userlog://appname:author:version')``.

    Arguments:
        appname (str): The name of the application.
        author (str): The name of the author (used on Windows).
        version (str): Optional version string, if a unique location
            per version of the application is required.
        roaming (bool): If `True`, use a *roaming* profile on
            Windows.
        create (bool): If `True` (the default) the directory
            will be created if it does not exist.

    """

    app_dir = 'user_log_dir'
