.. _globbing:

Globbing
========

Globbinng is the process of matching paths according to the rules used
by the Unix shell.

Generally speaking, you can think of a glob pattern as a path containing
one or more wildcard patterns. For instance ``"*.py"`` is a valid glob
pattern that will match all Python files in the current directory.


Matching Files and Directories
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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


Matching Directories
~~~~~~~~~~~~~~~~~~~~

You can specify that you only want to match a directory by appending
a forward slash to the pattern.

``**/.git/``
    Recursively matches all the git directories.


Glob Interface
==============

PyFilesystem supports globbing via the ``glob`` object on every FS instance.
Here's how you might use it to find all the Python files in your filesystem::

    for path, info in my_fs.glob("**/*.py"):
        print(path)

If you call ``.glob`` with a pattern it will return an iterator of every
path and corresponding :class:`~fs.info.Info` object of any matching path.


Glob Methods
~~~~~~~~~~~~

