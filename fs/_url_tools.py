import re
import six
import platform
import typing

if typing.TYPE_CHECKING:
    from typing import Text

_WINDOWS_PLATFORM = platform.system() == "Windows"


def url_quote(path_snippet):
    # type: (Text) -> Text
    """
    On Windows, it will separate drive letter and quote windows
    path alone. No magic on Unix-alie path, just pythonic
    `pathname2url`

    Arguments:
       path_snippet: a file path, relative or absolute.
    """
    if _WINDOWS_PLATFORM and _has_drive_letter(path_snippet):
        drive_letter, path = path_snippet.split(":", 1)
        if six.PY2:
            path = path.encode("utf-8")
        path = six.moves.urllib.request.pathname2url(path)
        path_snippet = "{}:{}".format(drive_letter, path)
    else:
        if six.PY2:
            path_snippet = path_snippet.encode("utf-8")
        path_snippet = six.moves.urllib.request.pathname2url(path_snippet)
    return path_snippet


def _has_drive_letter(path_snippet):
    # type: (Text) -> bool
    """
    The following path will get True
    D:/Data
    C:\\My Dcouments\\ test

    And will get False

    /tmp/abc:test

    Arguments:
       path_snippet: a file path, relative or absolute.
    """
    windows_drive_pattern = ".:[/\\\\].*$"
    return re.match(windows_drive_pattern, path_snippet) is not None
