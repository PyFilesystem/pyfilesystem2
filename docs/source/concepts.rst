Concepts
========

The following describes some core concepts when working with PyFilesystem.

Paths
-----

With the possible exception of the constructor, all paths in a filesystem are PyFilesystem paths, which are in the following format regardless of the platform:

 * Path components are separated by a forward slash (``/``)
 * Paths beginning with a ``/`` are *absolute* (start at the root of the FS)
 * Paths not beginning with a forward slash are relative
 * A single dot (``.``) means 'current directory'
 * A double dot (``..``) means 'previous directory'

Note that paths used by the FS interface will use this format, but the constructor or additional methods may not. Notably the :class:`fsosfs.OSFS` constructor which requires an OS path -- the format of which is platform-dependent.

.. note::
    There are many helpful functions for working with paths in the :mod:`fspath` module.

System Paths
------------

Not all Python modules can use file-like objects, especially those which interface with C libraries. For these situations you will need to retrieve the `system path` from an FS object you are working with. You can do this with the :meth:`fsbase.FS.getsyspath` method which converts a valid path in the context of the FS object to an absolute path that would be understood by your OS.

For example::

    >>> from fs.osfs import OSFS
    >>> home_fs = OSFS('~/')
    >>> home_fs.getsyspath('test.txt')
    '/home/will/test.txt'

Not all filesystems map to a system path (e.g. :class:`fsmemoryfs.MemoryFS`). If you call :meth:`fsbase.FS.getsyspath` on a filesystem which doesn't map to a system path, it will raise a :class:`fserrors.NoSysPath` exception.

Sandboxing
----------

FS objects are not permitted to work with any files outside of their *root*. If you attempt to open a file or directory outside the filesystem instance (with a backref such as ``"../foo.txt"``), a :class:`fserrors.IllegalBackReference` exception will be thrown. This ensures that any code using a FS object won't be able to read or modify anything you didn't intend it to and can limit the scope of any bugs.

Unlike your OS, there is no concept of a current working directory in PyFilesystem. If you want to work with a sub-directory of an FS object, you can use the :meth:`fsbase.FS.opendir` method which returns another FS object representing the contents of that sub-directory.

For example, consider the following directory structure. The directory ``foo`` contains two sub-directories; ``bar`` and ``baz``::

     --foo
       |--bar
       |  |--readme.txt
       |  `--photo.jpg
       `--baz
          |--private.txt
          `--dontopen.jpg

We can open the ``foo`` directory with the following code::

    from fs.osfs import OSFS
    foo_fs = OSFS('foo')

The ``foo_fs`` object can work with any of the contents of ``bar`` and ``baz``, which may not be desirable if we are passing ``foo_fs`` to a function that has the potential to delete files. Fortunately we can isolate a single sub-directory with the :meth:`fsbase.FS.opendir` method::

    bar_fs = foo_fs.opendir('bar')

This creates a completely new FS object that represents everything in the ``foo/bar`` directory. The root directory of ``bar_fs`` has been re-position, so that from ``bar_fs``'s point of view, the readme.txt and photo.jpg files are in the root::

    --bar
      |--readme.txt
      `--photo.jpg

.. note::
    This *sandboxing* only works if your code uses the filesystem interface exclusively. It won't prevent code using standard OS level file manipulation.


Errors
------

PyFilesystem converts errors in to a common exception hierarchy. This ensures that error handling code can be written once, regardless of the filesystem being used. See :mod:`fserrors` for details.
