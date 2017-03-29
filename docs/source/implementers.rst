.. _implementers:

实现文件系统
========================

有一点小心，你可以为任何文件系统实现一个PyFilesystem接口，这将允许它与任何内置的FS类和工具互换工作。

要创建一个PyFilesystem接口，从 :class:`~fs.base.FS` 派生一个类，并实现：ref：`essential-methods`。这应该给你一个工作的FS类。

注意复制方法签名，包括默认值。还必须遵循关于异常的相同逻辑，并且只在以下内容中引发异常 :mod:`~fs.errors` 。

构造函数
-----------

对于如何构造PyFilesystem类没有特别的要求，但是一定要调用没有参数的基类 ``__init__`` 方法。


线程安全
-------------

所有文件系统应该是 *线程安全* 。实现它的最简单的方法是使用 ``_lock`` 属性，它由 :class:`~fs.base.FS` 构造函数提供。这是一个来自标准库的 ``RLock`` 对象，可以用作上下文管理器，因此实现的方法将启动如下::

    with self._lock:
        do_something()

你不是 *必需* 使用 ``_lock`` 。只要在多线程的FS对象上调用方法不会破坏任何东西。

Python版本
---------------

PyFilesystem支持Python2.7和Python3.X。 两个主要Python版本之间的差异主要由 ``six`` 库管理。

在编写新的FS类时，您没有义务支持PyFilesystem的相同版本的Python，但是如果您的项目是一般使用的，则建议使用。


测试文件系统
-------------------

要测试您的实现，可以借用用于测试内置文件系统的测试套件。如果你的代码通过这些测试，那么你可以相信你的实现将无缝工作。

这里是测试一个名为 ``MyFS`` 的文件系统类的最简单的例子::

    from fs.test import FSTestCases

    class TestMyFS(FSTestCases):

        def make_fs(self):
            # Return an instance of your FS object here
            return MyFS()


您可能还想覆盖测试套件中的一些方法以进行更有针对性的测试:

.. autoclass:: fs.test.FSTestCases
    :members:

.. _essential-methods:

基本方法
-----------------

以下方法必须在PyFilesystem接口中实现。

* :meth:`~fs.base.FS.getinfo` 获取有关文件或目录的信息。
* :meth:`~fs.base.FS.listdir` 获取目录中的资源列表。
* :meth:`~fs.base.FS.makedir` 创建一个目录。
* :meth:`~fs.base.FS.openbin` 打开一个二进制文件。
* :meth:`~fs.base.FS.remove` 删除文件。
* :meth:`~fs.base.FS.removedir` 删除目录。
* :meth:`~fs.base.FS.setinfo` 设置资源信息。

.. _non-essential-methods:

非基本方法
-----------------------

以下方法可以在PyFilesystem接口中实现。

这些方法在基类中具有默认实现，但是如果您可以提供更优化的版本，则可以覆盖这些方法。

应该实现哪些方法取决于数据的存储方式和位置。 对于网络文件系统，一个好的候选实现，是 ``scandir`` 方法，否则为每个文件调用 ``listdir`` 和 ``getinfo`` 的组合。

在一般情况下，最好看看这些方法是如何实现的 :class:`~fs.base.FS` ，并且只写一个自定义版本，如果它比默认的更有效率。

* :meth:`~fs.base.FS.appendbytes`
* :meth:`~fs.base.FS.appendtext`
* :meth:`~fs.base.FS.close`
* :meth:`~fs.base.FS.copy`
* :meth:`~fs.base.FS.copydir`
* :meth:`~fs.base.FS.create`
* :meth:`~fs.base.FS.desc`
* :meth:`~fs.base.FS.exists`
* :meth:`~fs.base.FS.filterdir`
* :meth:`~fs.base.FS.getbytes`
* :meth:`~fs.base.FS.gettext`
* :meth:`~fs.base.FS.getmeta`
* :meth:`~fs.base.FS.getsize`
* :meth:`~fs.base.FS.getsyspath`
* :meth:`~fs.base.FS.gettype`
* :meth:`~fs.base.FS.geturl`
* :meth:`~fs.base.FS.hassyspath`
* :meth:`~fs.base.FS.hasurl`
* :meth:`~fs.base.FS.isclosed`
* :meth:`~fs.base.FS.isempty`
* :meth:`~fs.base.FS.isfile`
* :meth:`~fs.base.FS.lock`
* :meth:`~fs.base.FS.movedir`
* :meth:`~fs.base.FS.makedirs`
* :meth:`~fs.base.FS.move`
* :meth:`~fs.base.FS.open`
* :meth:`~fs.base.FS.opendir`
* :meth:`~fs.base.FS.removetree`
* :meth:`~fs.base.FS.scandir`
* :meth:`~fs.base.FS.setbytes`
* :meth:`~fs.base.FS.setbin`
* :meth:`~fs.base.FS.setfile`
* :meth:`~fs.base.FS.settimes`
* :meth:`~fs.base.FS.settext`
* :meth:`~fs.base.FS.touch`
* :meth:`~fs.base.FS.validatepath`

.. _helper-methods:

辅助方法
--------------

这些方法不应该实现。

实现这些可能不太值得的。

* :meth:`~fs.base.FS.getbasic`
* :meth:`~fs.base.FS.getdetails`
* :meth:`~fs.base.FS.check`
* :meth:`~fs.base.FS.match`
* :meth:`~fs.base.FS.tree`
