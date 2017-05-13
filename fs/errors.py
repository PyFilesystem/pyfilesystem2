"""

Defines the Exception classes thrown by PyFilesystem objects.

Errors relating to the underlying filesystem are translated in to one of
the following exceptions.

All Exception classes are derived from :class:`~fs.errors.FSError` which
may be used as a catch-all filesystem exception.

"""

from __future__ import unicode_literals
from __future__ import print_function

import six
from six import text_type

__all__ = [
    'CreateFailed',
    'DestinationExists',
    'DirectoryExists',
    'DirectoryExpected',
    'DirectoryNotEmpty',
    'FileExists',
    'FileExpected',
    'FilesystemClosed',
    'FSError',
    'IllegalBackReference',
    'InsufficientStorage',
    'InvalidCharsInPath',
    'InvalidPath',
    'NoURL',
    'OperationFailed',
    'OperationTimeout',
    'PathError',
    'PermissionDenied',
    'RemoteConnectionError',
    'RemoveRootError',
    'ResourceError',
    'ResourceInvalid',
    'ResourceLocked',
    'ResourceNotFound',
    'Unsupported',
]


@six.python_2_unicode_compatible
class FSError(Exception):
    """Base exception class for the FS module."""

    default_message = "Unspecified error"

    def __init__(self, msg=None):
        self._msg = msg or self.default_message
        super(FSError, self).__init__()

    def __str__(self):
        """The error message."""
        msg = self._msg.format(**self.__dict__)
        return msg

    def __repr__(self):
        msg = self._msg.format(**self.__dict__)
        return "{}({!r})".format(self.__class__.__name__, msg)


class FilesystemClosed(FSError):
    """An exception thrown when attempting to use a closed filesystem."""

    default_message = "attempt to use closed filesystem"


class CreateFailed(FSError):
    """An exception thrown when a FS could not be created."""

    default_message = "unable to create filesystem"


class PathError(FSError):
    """Exception for errors to do with a path string."""

    default_message = "path '{path}' is invalid"

    def __init__(self, path, msg=None):
        self.path = path
        super(PathError, self).__init__(msg=msg)


class NoSysPath(PathError):
    """Exception raised when there is no sys path."""

    default_message = "path '{path}' does not map to the local filesystem"


class NoURL(PathError):
    """Raised when there is no URL for a given path."""

    default_message = "path '{path}' has no '{purpose}' URL"

    def __init__(self, path, purpose, msg=None):
        self.purpose = purpose
        super(NoURL, self).__init__(path, msg=msg)


class InvalidPath(PathError):
    """Base exception for fs paths that can't be mapped on to the
    underlaying filesystem."""

    default_message = "path '{path}' is invalid on this filesystem "


class InvalidCharsInPath(InvalidPath):
    """The path contains characters that are invalid on this filesystem."""

    default_message = "path '{path}' contains invalid characters"


class OperationFailed(FSError):
    """Base exception class for errors associated with a specific operation."""

    default_message = "operation failed, {details}"

    def __init__(self, path=None, exc=None, msg=None):
        self.path = path
        self.exc = exc
        self.details = '' if exc is None else text_type(exc)
        self.errno = getattr(exc, "errno", None)
        super(OperationFailed, self).__init__(msg=msg)


class Unsupported(OperationFailed):
    """Exception raised for operations that are not supported by the FS."""

    default_message = "not supported"


class RemoteConnectionError(OperationFailed):
    """Exception raised when operations encounter remote connection trouble."""

    default_message = "remote connection error"


class InsufficientStorage(OperationFailed):
    """Exception raised when operations encounter storage space trouble."""

    default_message = "insufficient storage space"


class PermissionDenied(OperationFailed):
    """Permissions error."""

    default_message = "permission denied"


class OperationTimeout(OperationFailed):
    """Filesystem took too long."""

    default_message = "operation timed out"


class RemoveRootError(OperationFailed):
    """Attempt to remove the root directory."""

    default_message = "root directory may not be removed"


class ResourceError(FSError):
    """Base exception class for error associated with a specific resource."""

    default_message = "failed on path {path}"

    def __init__(self, path, exc=None, msg=None):
        self.path = path
        self.exc = exc
        super(ResourceError, self).__init__(msg=msg)


class ResourceNotFound(ResourceError):
    """Exception raised when a required resource is not found."""

    default_message = "resource '{path}' not found"


class ResourceInvalid(ResourceError):
    """Exception raised when a resource is the wrong type."""

    default_message = "resource '{path}' is invalid for this operation"


class FileExists(ResourceError):
    """Exception raises when opening a file in exclusive mode."""

    default_message = "resource '{path}' exists"


class FileExpected(ResourceInvalid):
    """Exception raises when a file was expected."""

    default_message = "path '{path}' should be a file"


class DirectoryExpected(ResourceInvalid):
    """Exception raises when a directory was expected."""

    default_message = "path '{path}' should be a directory"


class DestinationExists(ResourceError):
    """Exception raised when a target destination already exists."""

    default_message = "destination '{path}' exists"


class DirectoryExists(ResourceError):
    """Exception raised when trying to make a directory that already
    exists."""

    default_message = "directory '{path}' exists"


class DirectoryNotEmpty(ResourceError):
    """Exception raised when a directory to be removed is not empty."""

    default_message = "directory '{path}' is not empty"


class ResourceLocked(ResourceError):
    """Exception raised when a resource can't be used because it is locked."""

    default_message = "resource '{path}' is locked"


class ResourceReadOnly(ResourceError):
    """Raised when attempting to modify a read only resource."""

    default_message = "resource '{path}' is read only"


class IllegalBackReference(ValueError):
    """
    Exception raised when too many backrefs exist in a path.

    This error will occur if the back references in a path would be
    outside of the root. For example, ``"/foo/../../"``, contains two back
    references which would reference a directory above the root.

    .. note::

        This exception is a subclass of ``ValueError`` as it is not
        strictly speaking an issue with a filesystem or resource.

    """

    def __init__(self, path):
        _msg = \
            "path '{path}' contains back-references outside of filesystem"
        _msg = _msg.format(path=path)
        super(IllegalBackReference, self).__init__(_msg)
