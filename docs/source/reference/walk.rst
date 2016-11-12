fs.walk
=======

Walk a directory structure.

The ``Walker`` class in this module does the work of *walking* a filesystem. In other words, listing each resource in a directory, and any sub-directories.

To walk a filesystem (or directory) you can construct a :class::`fs.walk.Walker` object and use its methods to do the walking. Here's an example that prints the path to every Python file in your projects directory::

    >>> from fs import open_fs
    >>> from fs.walk import Walker
    >>> home_fs = open_fs('~/projects')
    >>> walker = Walker()
    >>> for path in walker.walk_files(home_fs, wildcards=['*.py']):
    ...     print(path)

Generally speaking, however, you will only need to construct a Walker object if you want to customize some behavior of the walking algorithm. This is because filesystem objects already have a walker attribute, which you can use as follows::

    >>> from fs import open_fs
    >>> home_fs = open_fs('~/projects')
    >>> for path in home_fs.walker.walk_files(wildcards=['*.py']):
    ...     print(path)

Note that the ``walk_files`` method above doesn't require a ``fs`` parameter. This is because the ``walker`` object has been *bound* to filesystem (see :meth:`fs.walk.Walker.bind`).


Search Methods
~~~~~~~~~~~~~~

There are two general algorithms for searching a directory tree. The first method is `"breadth"`, which yields resources in the top of the directory tree first, before moving on to sub-directories. The second is `"depth"` which yields the most deeply nested resources, and works backwards to the top-most directory.

Generally speaking, you will only need the a *depth* search if you will be deleting resources as you walk through them. The default *breadth* search is a generally more efficient way of looking through a filesystem. You can specify which method you want with the ``search`` parameter on most ``Walker`` methods.

.. automodule:: fs.walk
    :members: