Introduction
============

PyFilesystem is a Python module that provides a common interface to any
filesystem.

Think of PyFilesystem ``FS`` objects as the next logical step to
Python's ``file`` class. Just as *file-like* objects abstract a single
file, FS objects abstract the whole filesystem by providing a common
interface to operations such as listing directories, getting file
information, opening/copying/deleting files, etc.

Installing
----------

To install with pip, use the following::

    pip install fs

Or to upgrade to the most recent version::

    pip install fs --upgrade


You should now have the ``fs`` module on your path (version number may vary)::

    >>> import fs
    >>> fs.__version__
    '2.0.0'


Need Help?
----------

If you have any problems or questions, please contact the developers
through one of the following channels:

Bugs
####

If you find a bug in PyFilesystem, please file an issue:
http://code.google.com/p/pyfilesystem/issues/list

Discussion Group
################

There is also a discussion group for PyFilesystem:
http://groups.google.com/group/pyfilesystem-discussion

