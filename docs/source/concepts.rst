Concepts
========

The following describes some core concepts when working with
PyFilesystem. If you are skimming this documentation, pay particular
attention to the first section on paths.

Paths
-----

With the possible exception of the constructor, all paths in a
filesystem are *PyFilesystem paths*, which have the following
properties:

 * Paths are ``str`` type in Python3, and ``unicode`` in Python2
 * Path components are separated by a forward slash (``/``)
 * Paths beginning with a ``/`` are *absolute*
 * Paths not beginning with a forward slash are *relative*
 * A single dot (``.``) means 'current directory'
 * A double dot (``..``) means 'previous directory'

Note that paths used by the FS interface will use this format, but the
constructor may not. Notably the :class:`fs.osfs.OSFS` constructor which
requires an OS path -- the format of which is platform-dependent.

.. note::
    There are many helpful functions for working with paths in the
    :mod:`fs.path` module.

PyFilesystem paths are platform-independent, and will be automatically
converted to the format expected by your operating system -- so you
won't need to make any modifications to your filesystem code to make it
run on other platforms.

System Paths
------------

Not all Python modules can use file-like objects, especially those which
interface with C libraries. For these situations you will need to
retrieve the *system path*. You can do this with the
:meth:`fs.base.FS.getsyspath` method which converts a valid path in the
context of the FS object to an absolute path that would be understood by
your OS.

For example::

    >>> from fs.osfs import OSFS
    >>> home_fs = OSFS('~/')
    >>> home_fs.getsyspath('test.txt')
    '/home/will/test.txt'

Not all filesystems map to a system path (for example, files in a
:meth:`fs.memoryfs.MemoryFS` will only ever exists in memory).

If you call ``getsyspath`` on a filesystem which doesn't map to a system
path, it will raise a :meth:`fs.errors.NoSysPath` exception. If you
prefer a *look before you leap* approach, you can check if a resource
has a system path by calling :meth:`fs.base.FS.hassyspath`

Sandboxing
----------

FS objects are not permitted to work with any files outside of their
*root*. If you attempt to open a file or directory outside the
filesystem instance (with a backref such as ``"../foo.txt"``), a
:class:`fs.errors.IllegalBackReference` exception will be thrown. This
ensures that any code using a FS object won't be able to read or modify
anything you didn't intend it to, thus limiting the scope of any bugs.

Unlike your OS, there is no concept of a current working directory in
PyFilesystem. If you want to work with a sub-directory of an FS object,
you can use the :meth:`fs.base.FS.opendir` method which returns another
FS object representing the contents of that sub-directory.

For example, consider the following directory structure. The directory
``foo`` contains two sub-directories; ``bar`` and ``baz``::

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

The ``foo_fs`` object can work with any of the contents of ``bar`` and
``baz``, which may not be desirable if we are passing ``foo_fs`` to a
function that has the potential to delete files. Fortunately we can
isolate a single sub-directory with the :meth:`fs.base.FS.opendir`
method::

    bar_fs = foo_fs.opendir('bar')

This creates a completely new FS object that represents everything in
the ``foo/bar`` directory. The root directory of ``bar_fs`` has been re-
position, so that from ``bar_fs``'s point of view, the readme.txt and
photo.jpg files are in the root::

    --bar
      |--readme.txt
      `--photo.jpg

.. note::
    This *sandboxing* only works if your code uses the filesystem
    interface exclusively. It won't prevent code using standard OS level
    file manipulation.


Errors
------

PyFilesystem converts errors in to a common exception hierarchy. This
ensures that error handling code can be written once, regardless of the
filesystem being used. See :mod:`fs.errors` for details.
