.. _implementers:

Implementing Filesystems
========================

With a little care, you can implement a PyFilesystem interface for any filesystem, which will allow it to work interchangeably with any of the built-in FS classes and tools.

To create a PyFilesystem interface, derive a class from :class:`~fs.base.FS` and implement the :ref:`essential-methods`. This should give you a working FS class.

Take care to copy the method signatures *exactly*, including default values. It is also essential that you follow the same logic with regards to exceptions, and only raise exceptions in :mod:`~fs.errors`.

Constructor
-----------

There are no particular requirements regarding how a PyFilesystem class is constructed, but be sure to call the base class ``__init__`` method with no parameters.


Thread Safety
-------------

All Filesystems should be *thread-safe*. The simplest way to achieve that is by using the ``_lock`` attribute supplied by the :class:`~fs.base.FS` constructor. This is a ``RLock`` object from the standard library, which you can use as a context manager, so methods you implement will start something like this::

    with self._lock:
        do_something()

You aren't *required* to use ``_lock``. Just as long as calling methods on the FS object from multiple threads doesn't break anything.

Python Versions
---------------

PyFilesystem supports Python2.7 and Python3.X. The differences between the two major Python versions are largely managed by the ``six`` library.

You aren't obligated to support the same versions of Python that PyFilesystem itself supports, but it is recommended if your project is for general use.


Testing Filesystems
-------------------

To test your implementation, you can borrow the test suite used to test the built in filesystems. If your code passes these tests, then you can be confident your implementation will work seamlessly.

Here's the simplest possible example to test a filesystem class called ``MyFS``::

    from fs.test import FSTestCases

    class TestMyFS(FSTestCases):

        def make_fs(self):
            # Return an instance of your FS object here
            return MyFS()


You may also want to override some of the methods in the test suite for more targeted testing:

.. autoclass:: fs.test.FSTestCases
    :members:

.. note::

    As of version 2.4.11 this project uses `pytest <https://pytest.org/en/latest/>`_ to run its tests.
    While it's completely compatible with ``unittest``-style tests, it's much more powerful and
    feature-rich. We suggest you take advantage of it and its plugins in new tests you write, rather
    than sticking to strict ``unittest`` features. For benefits and limitations, see `here <https://pytest.org/en/latest/unittest.html>`_.


.. _essential-methods:

Essential Methods
-----------------

The following methods MUST be implemented in a PyFilesystem interface.

* :meth:`~fs.base.FS.getinfo` Get info regarding a file or directory.
* :meth:`~fs.base.FS.listdir` Get a list of resources in a directory.
* :meth:`~fs.base.FS.makedir` Make a directory.
* :meth:`~fs.base.FS.openbin` Open a binary file.
* :meth:`~fs.base.FS.remove` Remove a file.
* :meth:`~fs.base.FS.removedir` Remove a directory.
* :meth:`~fs.base.FS.setinfo` Set resource information.

.. _non-essential-methods:

Non - Essential Methods
-----------------------

The following methods MAY be implemented in a PyFilesystem interface.

These methods have a default implementation in the base class, but may be overridden if you can supply a more optimal version.

Exactly which methods you should implement depends on how and where the data is stored. For network filesystems, a good candidate to implement, is the ``scandir`` method which would otherwise call a combination of ``listdir`` and ``getinfo`` for each file.

In the general case, it is a good idea to look at how these methods are implemented in :class:`~fs.base.FS`, and only write a custom version if it would be more efficient than the default.

* :meth:`~fs.base.FS.appendbytes`
* :meth:`~fs.base.FS.appendtext`
* :meth:`~fs.base.FS.close`
* :meth:`~fs.base.FS.copy`
* :meth:`~fs.base.FS.copydir`
* :meth:`~fs.base.FS.create`
* :meth:`~fs.base.FS.desc`
* :meth:`~fs.base.FS.download`
* :meth:`~fs.base.FS.exists`
* :meth:`~fs.base.FS.filterdir`
* :meth:`~fs.base.FS.getmeta`
* :meth:`~fs.base.FS.getospath`
* :meth:`~fs.base.FS.getsize`
* :meth:`~fs.base.FS.getsyspath`
* :meth:`~fs.base.FS.gettype`
* :meth:`~fs.base.FS.geturl`
* :meth:`~fs.base.FS.hassyspath`
* :meth:`~fs.base.FS.hasurl`
* :meth:`~fs.base.FS.isclosed`
* :meth:`~fs.base.FS.isempty`
* :meth:`~fs.base.FS.isdir`
* :meth:`~fs.base.FS.isfile`
* :meth:`~fs.base.FS.islink`
* :meth:`~fs.base.FS.lock`
* :meth:`~fs.base.FS.makedirs`
* :meth:`~fs.base.FS.move`
* :meth:`~fs.base.FS.movedir`
* :meth:`~fs.base.FS.open`
* :meth:`~fs.base.FS.opendir`
* :meth:`~fs.base.FS.readbytes`
* :meth:`~fs.base.FS.readtext`
* :meth:`~fs.base.FS.removetree`
* :meth:`~fs.base.FS.scandir`
* :meth:`~fs.base.FS.settimes`
* :meth:`~fs.base.FS.touch`
* :meth:`~fs.base.FS.upload`
* :meth:`~fs.base.FS.validatepath`
* :meth:`~fs.base.FS.writebytes`
* :meth:`~fs.base.FS.writefile`
* :meth:`~fs.base.FS.writetext`

.. _helper-methods:

Helper Methods
--------------

These methods SHOULD NOT be implemented.

Implementing these is highly unlikely to be worthwhile.

* :meth:`~fs.base.FS.check`
* :meth:`~fs.base.FS.getbasic`
* :meth:`~fs.base.FS.getdetails`
* :meth:`~fs.base.FS.hash`
* :meth:`~fs.base.FS.match`
* :meth:`~fs.base.FS.tree`
