"""
A collection of filesystems that map to application specific locations
defined by the OS.

These classes abstract away the different requirements for user data
across platforms, which vary in their conventions. They are all
subclasses of :class:`~fs.osfs.OSFS`.

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
    """
    Abstract base class for an app FS.

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
    """
    A filesystem for per-user application data.

    :param str appname: The name of the application.
    :param str author: The name of the author (used on Windows).
    :param str version: Optional version string, if a unique location
        per version of the application is required.
    :param bool roaming: If ``True``, use a *roaming* profile on
        Windows.
    :param bool create: If ``True`` (the default) the directory will
        be created if it does not exist.

    """
    app_dir = 'user_data_dir'


class UserConfigFS(_AppFS):
    """
    A filesystem for per-user config data.

    :param str appname: The name of the application.
    :param str author: The name of the author (used on Windows).
    :param str version: Optional version string, if a unique location
        per version of the application is required.
    :param bool roaming: If ``True``, use a *roaming* profile on
        Windows.
    :param bool create: If ``True`` (the default) the directory will
        be created if it does not exist.

    """
    app_dir = 'user_config_dir'


class UserCacheFS(_AppFS):
    """
    A filesystem for per-user application cache data.

    :param str appname: The name of the application.
    :param str author: The name of the author (used on Windows).
    :param str version: Optional version string, if a unique location
        per version of the application is required.
    :param bool roaming: If ``True``, use a *roaming* profile on
        Windows.
    :param bool create: If ``True`` (the default) the directory will
        be created if it does not exist.

    """
    app_dir = 'user_cache_dir'


class SiteDataFS(_AppFS):
    """
    A filesystem for application site data.

    :param str appname: The name of the application.
    :param str author: The name of the author (used on Windows).
    :param str version: Optional version string, if a unique location
        per version of the application is required.
    :param bool roaming: If ``True``, use a *roaming* profile on
        Windows.
    :param bool create: If ``True`` (the default) the directory will
        be created if it does not exist.

    """
    app_dir = 'site_data_dir'


class SiteConfigFS(_AppFS):
    """
    A filesystem for application config data.

    :param str appname: The name of the application.
    :param str author: The name of the author (used on Windows).
    :param str version: Optional version string, if a unique location
        per version of the application is required.
    :param bool roaming: If ``True``, use a *roaming* profile on
        Windows.
    :param bool create: If ``True`` (the default) the directory will
        be created if it does not exist.

    """
    app_dir = 'site_config_dir'


class UserLogFS(_AppFS):
    """
    A filesystem for per-user application log data.

    :param str appname: The name of the application.
    :param str author: The name of the author (used on Windows).
    :param str version: Optional version string, if a unique location
        per version of the application is required.
    :param bool roaming: If ``True``, use a *roaming* profile on
        Windows.
    :param bool create: If ``True`` (the default) the directory will
        be created if it does not exist.

    """
    app_dir = 'user_log_dir'
