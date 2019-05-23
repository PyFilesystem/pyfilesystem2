..  _walking:

Walking
=======

*Walking* a filesystem means recursively visiting a directory and any sub-directories. It is a fairly common requirement for copying, searching etc.

To walk a filesystem (or directory) you can construct a :class:`~fs.walk.Walker` object and use its methods to do the walking. Here's an example that prints the path to every Python file in your projects directory::

    >>> from fs import open_fs
    >>> from fs.walk import Walker
    >>> home_fs = open_fs('~/projects')
    >>> walker = Walker(filter=['*.py'])
    >>> for path in walker.files(home_fs):
    ...     print(path)

Generally speaking, however, you will only need to construct a Walker object if you want to customize some behavior of the walking algorithm. This is because you can access the functionality of a Walker object via the ``walk`` attribute on FS objects. Here's an example::

    >>> from fs import open_fs
    >>> home_fs = open_fs('~/projects')
    >>> for path in home_fs.walk.files(filter=['*.py']):
    ...     print(path)

Note that the ``files`` method above doesn't require a ``fs`` parameter. This is because the ``walk`` attribute is a property which returns a :class:`~fs.walk.BoundWalker` object, which associates the filesystem with a walker.

Walk Methods
~~~~~~~~~~~~

If you call the ``walk`` attribute on a :class:`~fs.walk.BoundWalker` it will return an iterable of :class:`~fs.walk.Step` named tuples with three values; a path to the directory, a list of :class:`~fs.info.Info` objects for directories, and a list of :class:`~fs.info.Info` objects for the files. Here's an example::

    for step in home_fs.walk(filter=['*.py']):
        print('In dir {}'.format(step.path))
        print('sub-directories: {!r}'.format(step.dirs))
        print('files: {!r}'.format(step.files))

.. note ::
    Methods of  :class:`~fs.walk.BoundWalker` invoke a corresponding method on a :class:`~fs.walk.Walker` object, with the *bound* filesystem.

The ``walk`` attribute may appear to be a method, but is in fact a callable object. It supports other convenient methods that supply different information from the walk. For instance, :meth:`~fs.walk.BoundWalker.files`, which returns an iterable of file paths. Here's an example::

    for path in home_fs.walk.files(filter=['*.py']):
        print('Python file: {}'.format(path))

The complement to ``files`` is :meth:`~fs.walk.BoundWalker.dirs` which returns paths to just the directories (and ignoring the files). Here's an example::

    for dir_path in home_fs.walk.dirs():
        print("{!r} contains sub-directory {}".format(home_fs, dir_path))

The :meth:`~fs.walk.BoundWalker.info` method returns a generator of tuples containing a path and an :class:`~fs.info.Info` object. You can use the ``is_dir`` attribute to know if the path refers to a directory or file. Here's an example::

    for path, info in home_fs.walk.info():
        if info.is_dir:
            print("[dir] {}".format(path))
        else:
            print("[file] {}".format(path))

Finally, here's a nice example that counts the number of bytes of Python code in your home directory::

    bytes_of_python = sum(
        info.size
        for info in home_fs.walk.info(namespaces=['details'])
        if not info.is_dir
    )


Search Algorithms
~~~~~~~~~~~~~~~~~

There are two general algorithms for searching a directory tree. The first method is `"breadth"`, which yields resources in the top of the directory tree first, before moving on to sub-directories. The second is `"depth"` which yields the most deeply nested resources, and works backwards to the top-most directory.

Generally speaking, you will only need the a *depth* search if you will be deleting resources as you walk through them. The default *breadth* search is a generally more efficient way of looking through a filesystem. You can specify which method you want with the ``search`` parameter on most ``Walker`` methods.
