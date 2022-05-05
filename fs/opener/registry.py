# coding: utf-8
"""`Registry` class mapping protocols and FS URLs to their `Opener`.
"""

from __future__ import absolute_import, print_function, unicode_literals

import typing

import collections
import contextlib
import pkg_resources

from ..errors import ResourceReadOnly
from .base import Opener
from .errors import EntryPointError, UnsupportedProtocol
from .parse import parse_fs_url

if typing.TYPE_CHECKING:
    from typing import Callable, Dict, Iterator, List, Text, Tuple, Type, Union

    from ..base import FS


class Registry(object):
    """A registry for `Opener` instances."""

    def __init__(self, default_opener="osfs", load_extern=False):
        # type: (Text, bool) -> None
        """Create a registry object.

        Arguments:
            default_opener (str, optional): The protocol to use, if one
                is not supplied. The default is to use 'osfs', so that the
                FS URL is treated as a system path if no protocol is given.
            load_extern (bool, optional): Set to `True` to load openers from
                PyFilesystem2 extensions. Defaults to `False`.

        """
        self.default_opener = default_opener
        self.load_extern = load_extern
        self._protocols = {}  # type: Dict[Text, Opener]

    def __repr__(self):
        # type: () -> Text
        return "<fs-registry {!r}>".format(self.protocols)

    def install(self, opener):
        # type: (Union[Type[Opener], Opener, Callable[[], Opener]]) -> Opener
        """Install an opener.

        Arguments:
            opener (`Opener`): an `Opener` instance, or a callable that
                returns an opener instance.

        Note:
            May be used as a class decorator. For example::

                registry = Registry()
                @registry.install
                class ArchiveOpener(Opener):
                    protocols = ['zip', 'tar']

        """
        _opener = opener if isinstance(opener, Opener) else opener()
        assert isinstance(_opener, Opener), "Opener instance required"
        assert _opener.protocols, "must list one or more protocols"
        for protocol in _opener.protocols:
            self._protocols[protocol] = _opener
        return _opener

    @property
    def protocols(self):
        # type: () -> List[Text]
        """`list`: the list of supported protocols."""
        _protocols = list(self._protocols)
        if self.load_extern:
            _protocols.extend(
                entry_point.name
                for entry_point in pkg_resources.iter_entry_points("fs.opener")
            )
            _protocols = list(collections.OrderedDict.fromkeys(_protocols))
        return _protocols

    def get_opener(self, protocol):
        # type: (Text) -> Opener
        """Get the opener class associated to a given protocol.

        Arguments:
            protocol (str): A filesystem protocol.

        Returns:
            Opener: an opener instance.

        Raises:
            ~fs.opener.errors.UnsupportedProtocol: If no opener
                could be found for the given protocol.
            EntryPointLoadingError: If the returned entry point
                is not an `Opener` subclass or could not be loaded
                successfully.

        """
        protocol = protocol or self.default_opener

        if self.load_extern:
            entry_point = next(
                pkg_resources.iter_entry_points("fs.opener", protocol), None
            )
        else:
            entry_point = None

        # If not entry point was loaded from the extensions, try looking
        # into the registered protocols
        if entry_point is None:
            if protocol in self._protocols:
                opener_instance = self._protocols[protocol]
            else:
                raise UnsupportedProtocol(
                    "protocol '{}' is not supported".format(protocol)
                )

        # If an entry point was found in an extension, attempt to load it
        else:
            try:
                opener = entry_point.load()
            except Exception as exception:
                raise EntryPointError(
                    "could not load entry point; {}".format(exception)
                )
            if not issubclass(opener, Opener):
                raise EntryPointError("entry point did not return an opener")

            try:
                opener_instance = opener()
            except Exception as exception:
                raise EntryPointError(
                    "could not instantiate opener; {}".format(exception)
                )

        return opener_instance

    def open(
        self,
        fs_url,  # type: Text
        writeable=True,  # type: bool
        create=False,  # type: bool
        cwd=".",  # type: Text
        default_protocol="osfs",  # type: Text
    ):
        # type: (...) -> Tuple[FS, Text]
        """Open a filesystem from a FS URL.

        Returns a tuple of a filesystem object and a path. If there is
        no path in the FS URL, the path value will be `None`.

        Arguments:
            fs_url (str): A filesystem URL.
            writeable (bool, optional): `True` if the filesystem must be
                writeable.
            create (bool, optional): `True` if the filesystem should be
                created if it does not exist.
            cwd (str): The current working directory.

        Returns:
            (FS, str): a tuple of ``(<filesystem>, <path from url>)``

        """
        if "://" not in fs_url:
            # URL may just be a path
            fs_url = "{}://{}".format(default_protocol, fs_url)

        parse_result = parse_fs_url(fs_url)
        protocol = parse_result.protocol
        open_path = parse_result.path

        opener = self.get_opener(protocol)

        open_fs = opener.open_fs(fs_url, parse_result, writeable, create, cwd)
        return open_fs, open_path

    def open_fs(
        self,
        fs_url,  # type: Union[FS, Text]
        writeable=False,  # type: bool
        create=False,  # type: bool
        cwd=".",  # type: Text
        default_protocol="osfs",  # type: Text
    ):
        # type: (...) -> FS
        """Open a filesystem from a FS URL (ignoring the path component).

        Arguments:
            fs_url (str): A filesystem URL. If a filesystem instance is
                given instead, it will be returned transparently.
            writeable (bool, optional): `True` if the filesystem must
                be writeable.
            create (bool, optional): `True` if the filesystem should be
                created if it does not exist.
            cwd (str): The current working directory (generally only
                relevant for OS filesystems).
            default_protocol (str): The protocol to use if one is not
                supplied in the FS URL (defaults to ``"osfs"``).

        Returns:
            ~fs.base.FS: A filesystem instance.

        Caution:
            The ``writeable`` parameter only controls whether the
            filesystem *needs* to be writable, which is relevant for
            some archive filesystems. Passing ``writeable=False`` will
            **not** make the return filesystem read-only. For this,
            consider using `fs.wrap.read_only` to wrap the returned
            instance.

        """
        from ..base import FS

        if isinstance(fs_url, FS):
            _fs = fs_url
        else:
            _fs, _path = self.open(
                fs_url,
                writeable=writeable,
                create=create,
                cwd=cwd,
                default_protocol=default_protocol,
            )
        return _fs

    @contextlib.contextmanager
    def manage_fs(
        self,
        fs_url,  # type: Union[FS, Text]
        create=False,  # type: bool
        writeable=False,  # type: bool
        cwd=".",  # type: Text
    ):
        # type: (...) -> Iterator[FS]
        """Get a context manager to open and close a filesystem.

        Arguments:
            fs_url (FS or str): A filesystem instance or a FS URL.
            create (bool, optional): If `True`, then create the filesystem if
                it doesn't already exist.
            writeable (bool, optional): If `True`, then the filesystem
                must be writeable.
            cwd (str): The current working directory, if opening a
                `~fs.osfs.OSFS`.

        Sometimes it is convenient to be able to pass either a FS object
        *or* an FS URL to a function. This context manager handles the
        required logic for that.

        Example:
            The `~Registry.manage_fs` method can be used to define a small
            utility function::

                >>> def print_ls(list_fs):
                ...     '''List a directory.'''
                ...     with manage_fs(list_fs) as fs:
                ...         print(' '.join(fs.listdir()))

            This function may be used in two ways. You may either pass
            a ``str``, as follows::

                >>> print_list('zip://projects.zip')

            Or, an filesystem instance::

                >>> from fs.osfs import OSFS
                >>> projects_fs = OSFS('~/')
                >>> print_list(projects_fs)

        """
        from ..base import FS

        def assert_writeable(fs):
            if fs.getmeta().get("read_only", True):
                raise ResourceReadOnly(path="/")

        if isinstance(fs_url, FS):
            if writeable:
                assert_writeable(fs_url)
            yield fs_url
        else:
            _fs = self.open_fs(fs_url, create=create, writeable=writeable, cwd=cwd)
            if writeable:
                assert_writeable(_fs)
            try:
                yield _fs
            finally:
                _fs.close()


registry = Registry(load_extern=True)
