from contextlib import contextmanager

from .. import errors


@contextmanager
def raise_os():
    try:
        yield
    except errors.ResourceNotFound as error:
        if PY2:
            raise IOError(2, "No such file or directory")
        else:
            raise FileNotFoundError(2, "No such file or directory: {!r}".format(error.path))
