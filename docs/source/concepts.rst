..  _concepts:

概念
========

下面介绍使用PyFilesystem时的一些核心概念。 如果你在阅读本文档，请特别注意路径的第一部分。

..  _paths:

路径
-----

除了构造函数可能例外，文件系统中的所有路径都是 *PyFilesystem paths* ，它们具有以下属性：

 * 路径在Python3中是 ``str`` 类型，在Python2中是 ``unicode``
 * 路径组件由正斜杠（ ``/`` ）分隔
 * 以 ``/`` 开头的路径是 *绝对路径*
 * 不以正斜杠开头的路径是 *相对路径*
 * 单个点（ ``.`` ）意味着 ``当前目录``
 * 双点（ ``..`` ）意味着 ``上级目录``

请注意，FS接口使用的路径将使用此格式，但构造函数可能不使用。 值得注意的是 :class:`~fs.osfs.OSFS` 构造函数，它需要一个操作系统路径 - 其格式是平台相关的。

.. note::
    在 :mod:`~fs.path` 模块中有许多有用的函数用于处理路径。

PyFilesystem路径是与平台无关的，并且会自动转换为操作系统预期的格式 - 因此您不需要对文件系统代码进行任何修改，以使其在其他平台上运行。

系统路径
------------

不是所有的Python模块都可以使用类似文件的对象，特别是那些与C库接口的对象。 对于这些情况，您将需要检索 *系统路径* 。您可以使用 :meth:`~fs.base.FS.getsyspath` 方法，将FS对象上下文中的有效路径转换为操作系统可以理解的绝对路径。

例如::

    >>> from fs.osfs import OSFS
    >>> home_fs = OSFS('~/')
    >>> home_fs.getsyspath('test.txt')
    '/home/will/test.txt'

不是所有的文件系统都映射到系统路径（例如： :class:`~fs.memoryfs.MemoryFS` 中的文件将只存在于内存中）。

如果你在一个不映射到系统路径的文件系统上调用 ``getsyspath`` ，它将引发一个 :meth:`~fs.errors.NoSysPath` 异常。如果你喜欢跳回之前看的内容，你可以通过调用 :meth:`~fs.base.FS.hassyspath` 来检查资源是否有系统路径。


沙盒
----------

FS对象不允许使用其 *root* 之外的任何文件。如果你试图打开文件系统实例之外的文件或目录（带有一个上级引用，如 ``"../ foo.txt"`` ），那么将抛出 :class:`~fs.errors.IllegalBackReference` 异常。这确保任何使用FS对象的代码将无法读取或修改您不想要的任何内容，从而限制任何出错范围。

与您的操作系统不同，PyFilesystem中没有当前工作目录的概念。如果要使用FS对象的子目录，可以使用 :meth:`~fs.base.FS.opendir` 方法，该方法返回表示该子目录的内容的另一个FS对象。

例如，考虑以下目录结构。目录 ``foo`` 包含两个子目录; ``bar`` 和 ``baz`` ::

     --foo
       |--bar
       |  |--readme.txt
       |  `--photo.jpg
       `--baz
          |--private.txt
          `--dontopen.jpg

我们可以用下面的代码打开 ``foo`` 目录::

    from fs.osfs import OSFS
    foo_fs = OSFS('foo')

如果我们传递 ``foo_fs`` 一个有可能会删除文件的函数,``foo_fs`` 对象可以使用 ``bar`` 和 ``baz`` 的任何内容可能不是所期望的。幸运的是我们可以用一个子目录 :meth:`~fs.base.FS.opendir` 方法::

    bar_fs = foo_fs.opendir('bar')

这将创建一个全新的FS对象，代表 ``foo / bar`` 目录中的所有内容。 ``bar_fs`` 的根目录已经被重新定位，所以从 ``bar_fs`` 的角度来看，readme.txt和photo.jpg文件在根目录下::

    --bar
      |--readme.txt
      `--photo.jpg

.. note::
    *沙箱* 只在你的代码使用本模块的文件系统接口时才有效。 它不会阻止使用标准操作系统级别文件操作的代码。

错误
------

PyFilesystem将错误转换为公共异常层次结构。 这确保错误处理代码可以写入一次，而不管使用的文件系统。 有关详细信息，请参阅 :mod:`~fs.errors` 。
