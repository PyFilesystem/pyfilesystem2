"""

Defines the Exception classes thrown by PyFilesystem objects.

Errors relating to the underlying filesystem are translated in to one of
the following exceptions.

All Exception classes are derived from `FSError` which can be used as a
catch-all.

"""

from __future__ import unicode_literals
from __future__ import print_function

import six
from six import text_type

__all__ = [
    'CreateFailed',
    'DestinationExists',
    'DirectoryExists',
    'DirectoryNotEmpty',
    'FilesystemClosed',
    'FSError',
    'IllegalBackReference',
    'InsufficientStorage',
    'InvalidCharsInPath',
    'InvalidPath',
    'NotADirectory',
    'NoURL',
    'OperationFailed',
    'OperationTimeout',
    'ParentDirectoryMissing',
    'PathError',
    'PermissionDenied',
    'RemoteConnectionError',
    'RemoveRootFail',
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
        if msg is None:
            msg = self.default_message.format(**self.__dict__)
        self.msg = msg
        super(FSError, self).__init__(msg)

    def __str__(self):
        """The error message."""
        return self.msg


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

    default_message = "path '{path}' has no URL"


class InvalidPath(PathError):
    """Base exception for fs paths that can't be mapped on to the
    underlaying filesystem."""

    default_message = "path '{path}' is invalid on this filesystem "


class InvalidCharsInPath(InvalidPath):
    """The path contains characters that are invalid on this filesystem."""

    default_message = "path '{path}' contains invalid characters"


class OperationFailed(FSError):
    """Base exception class for errors associated with a specific operation."""

    default_message = "operation {opname} failed, {details}"

    def __init__(self, path=None, opname="", exc=None):
        self.path = path
        self.opname = opname
        self.exc = exc
        self.details = '' if exc is None else text_type(exc)
        self.errno = getattr(exc, "errno", None)
        super(OperationFailed, self).__init__()


class ReadOnly(FSError):
    """Raised when a filesystem doesn't support writing."""
    default_message = "filesystem is read-only"


class Unsupported(OperationFailed):
    """Exception raised for operations that are not supported by the FS."""

    default_message = "operation '{opname}' is unsupported by this filesystem"

    def __init__(self, opname):
        self.opname = opname
        super(Unsupported, self).__init__()


class RemoteConnectionError(OperationFailed):
    """Exception raised when operations encounter remote connection trouble."""

    default_message = "operation '{opname}' failed, remote connection error"


class InsufficientStorage(OperationFailed):
    """Exception raised when operations encounter storage space trouble."""

    default_message = "operation '{opname}' failed, insufficient storage space"


class PermissionDenied(OperationFailed):
    """Permissions error."""

    default_message = "operation {opname} failed, permission denied"


class OperationTimeout(OperationFailed):
    """Filesystem took too long."""

    default_message = "operation '{opname}' failed, operation timed out"


class RemoveRootFail(OperationFailed):
    """Attempt to remove the root directory."""

    default_message = "root directory may not be removed"


class ResourceError(FSError):
    """Base exception class for error associated with a specific resource."""

    default_message = "operation '{opname}' failed on path {path}"

    def __init__(self, path, opname='', exc=None, msg=None):
        self.path = path
        self.opname = opname
        self.exc = exc
        super(ResourceError, self).__init__(msg=msg)


class Failed(ResourceError):
    """Raised when an operation failed on a resource."""

    default_message = "operation '{}' failed on '{}'"


class ResourceNotFound(ResourceError):
    """Exception raised when a required resource is not found."""

    default_message = "resource '{path}' not found"


class ResourceInvalid(ResourceError):
    """Exception raised when a resource is the wrong type."""

    default_message = "resource '{path}' is invalid for this operation"


class DirectoryNotExpected(ResourceInvalid):
    """Exception raise when attempting to remove a directory."""

    default_message = "path '{path}' should not be a directory"


class DirectoryExpected(ResourceInvalid):
    """Exception raise when attempting to remove a directory."""

    default_message = "path '{path}' should be  directory"


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


class ParentDirectoryMissing(ResourceError):
    """Exception raised when a parent directory is missing."""

    default_message = "a parent directory is missing for path '{path}'"


class NotADirectory(ResourceError):
    """Exception raised when a path should be an directory."""

    default_message = "ancestor in '{path}' is not a directory"


class ResourceLocked(ResourceError):
    """Exception raised when a resource can't be used because it is locked."""

    default_message = "resource '{path}' is locked"


class ResourceReadOnly(ResourceError):
    """Raised when attempting to modify a read only resource."""

    default_message = "resource '{path}' is read only"


class IllegalBackReference(ValueError):
    """Exception raised when too many backrefs exist in a path.

    This error will occur if the back references in a path would be
    outside of the root. For example, "/foo/../../", contains two back
    references which would reference a directory above the root.

    .. note:

    This exception is a subclass of ``ValueError`` as it is not
    strictly speaking an issue with a filesystem or resource.

    """

    def __init__(self, path):
        _msg = \
            "path '{path}' contains back-references outside of filesystem"
        _msg = _msg.format(path=path)
        super(IllegalBackReference, self).__init__(_msg)
