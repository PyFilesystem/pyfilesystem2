..  _walking:

walk
=======

*walk* 文件系统意味着递归地访问目录和任何子目录。这是复制，搜索等相当普遍的要求。

要走一个文件系统（或目录），你可以构造一个 :class:`~fs.walk.Walker` 对象，并使用它的方法来做行走。下面是一个打印项目目录中每个Python文件的路径的示例::

    >>> from fs import open_fs
    >>> from fs.walk import Walker
    >>> home_fs = open_fs('~/projects')
    >>> walker = Walker(filter=['*.py'])
    >>> for path in walker.files(home_fs):
    ...     print(path)

然而，一般来说，如果你想定制步行算法的某些行为，你只需要构造一个Walker对象。这是因为你可以通过FS对象的 ``walk`` 属性来访问Walker对象的功能。下面是一个例子::

    >>> from fs import open_fs
    >>> home_fs = open_fs('~/projects')
    >>> for path in home_fs.walk.files(filter=['*.py']):
    ...     print(path)

注意上面的 ``files`` 方法不需要 ``fs`` 参数。 这是因为 ``walk`` 属性是一个属性，它返回一个 :class:`~fs.walk.BoundWalker` 对象，它将文件系统与一个walker相关联。

walk 方法
~~~~~~~~~~~~

如果你在一个 :class:`~fs.walk.BoundWalker` 上调用 ``walk`` 属性，它将返回一个可迭代的 :class:`~fs.walk.Step` 命名tuples有三个值;目录的路径，目录的一个列表 :class:`~fs.info.Info` 对象，以及一个 :class:`~fs.info.Info` 对象的列表。下面是一个例子::

    for step in home_fs.walk(filter=['*.py']):
        print('In dir {}'.format(step.path))
        print('sub-directories: {!r}'.format(step.dirs))
        print('files: {!r}'.format(step.files))

.. Note ::
    方法 :class:`~fs.walk.BoundWalker` 在 :class:`~fs.walk.Walker` 对象上调用相应的方法，使用 *bound* 文件系统。

``walk`` 属性可能看起来是一个方法，但实际上是一个可调用的对象。它支持从步行提供不同信息的其他方便的方法。例如 :class:`~fs.walk.BoundWalker.files`，它返回一个可迭代的文件路径。下面是一个例子::

    for path in home_fs.walk.files(filter=['*.py']):
        print('Python file: {}'.format(path))

``files`` 的称号是 :meth:`~fs.walk.BoundWalker.dirs` ，它只返回目录的路径（忽略文件）。下面是一个例子::

    for dir_path in home_fs.walk.dirs():
        print("{!r} contains sub-directory {}".format(home_fs, dir_path))

:meth:`~fs.walk.BoundWalker.info` 方法返回一个包含一个路径和一个 :class:`~fs.info.Info` 对象的元组生成器。您可以使用 ``is_dir`` 属性来了解路径是否指向目录或文件。下面是一个例子::

    for path, info in home_fs.walk.info():
        if info.is_dir:
            print("[dir] {}".format(path))
        else:
            print("[file] {}".format(path))

最后，下面是一个很好的例子，它计算你的主目录中的Python代码的字节数::

    bytes_of_python = sum(
        info.size
        for info in home_fs.walk.info(namespaces=['details'])
        if not info.is_dir
    )

搜索算法
~~~~~~~~~~~~~~~~~

有两种用于搜索目录树的通用算法。第一种方法是“breadth”，它首先在目录树的顶部产生资源，然后进入子目录。第二个是“深度”，它产生最深的嵌套资源，并向后工作到最顶层目录。

一般来说，你只需要一个 *depth* 搜索，如果你将通过它们删除资源。默认 *宽度* 搜索是一种通常更有效的方式查看文件系统。你可以在大多数“Walker”方法中使用 ``search`` 参数指定你想要的方法。
