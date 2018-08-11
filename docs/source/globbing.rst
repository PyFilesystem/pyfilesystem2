.. _globbing:

Globbing
========

Globbing is the process of matching paths according to the rules used
by the Unix shell.

Generally speaking, you can think of a glob pattern as a path containing
one or more wildcard patterns, separated by forward slashes.


Matching Files and Directories
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In a glob pattern, A ``*`` means match anything text in a filename. A ``?``
matches any single character. A ``**`` matches any number of subdirectories,
making the glob *recusrive*. If the glob pattern ends in a ``/``, it will
only match directory paths, otherwise it will match files and directories.

.. note::
    A recursive glob requires that PyFilesystem scan a lot of files,
    and can potentially be slow for large (or network based) filesystems.

Here's a summary of glob patterns:

``*``
    Matches all files in the current directory.
``*.py``
    Matches all .py file in the current directory.
``*.py?``
    Matches all .py files and .pyi, .pyc etc in the currenct directory.
``project/*.py``
    Matches all .py files in a directory called ``project``.
``*/*.py``
    Matches all .py files in any sub directory.
``**/*.py``
    Recursively matches all .py files.
``**/.git/``
    Recursively matches all the git directories.


Interface
~~~~~~~~~

PyFilesystem supports globbing via the ``glob`` attribute on every FS
instance, which is an instance of :class:`~fs.glob.BoundGlobber`. Here's
how you might use it to find all the Python files in your filesystem::

    for path, info in my_fs.glob("**/*.py"):
        print(path)

Calling ``.glob`` with a pattern will return an iterator of every
path and corresponding :class:`~fs.info.Info` for each matched file and
directory.


Batch Methods
~~~~~~~~~~~~~

In addition to iterating over the results, you can also call methods on
the :class:`~fs.glob.Globber` which apply to every matched path.

For instance, here is how you can use glob to remove all ``.pyc`` files
from a project directory::

    >>> import fs
    >>> fs.open_fs('~/projects/my_project').glob('**/*.pyc').remove()
    29

