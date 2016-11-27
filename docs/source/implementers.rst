.. _implementers:

Implementing Filesystems
========================

With a little care, you can implement a PyFilesystem interface for any filesystem, which will allow it to work interchangeably with any of the built-in FS classes and tools.

To create a PyFilesystem interface, derive a class from :class:`fs.base.FS` and implement the seven :ref:`essential-methods`. This should give you a working FS class.

Take care to copy the method signatures *exactly*, including default values. It is also essential that you follow the same logic with regards to exceptions, and only raise exceptions in :mod:`fs.errors`.

Constructor
-----------

There are no particular requirements regarding how a PyFilesystem class is constructed, but be sure to call the base class ``__init__`` method with no parameters.


Testing Filesystems
-------------------




.. _essential-methods:

Essential Methods
-----------------

The following methods MUST be implemented in a PyFilesystem interface.

* :meth:`fs.base.FS.getinfo` Get info regarding a file or directory.
* :meth:`fs.base.FS.listdir` Get a list of resources in a directory.
* :meth:`fs.base.FS.makedir` Make a directory.
* :meth:`fs.base.FS.openbin` Open a binary file.
* :meth:`fs.base.FS.remove` Remove a file.
* :meth:`fs.base.FS.removedir` Remove a directory.
* :meth:`fs.base.FS.setinfo` Set resource information.

.. _non-essential-methods:

Non - Essential Methods
-----------------------

The following methods MAY be implemented in a PyFilesystem interface.

These methods have a default implementation, but may be overridden if you can supply a more optimal version. For instance the ``getbytes`` method opens a file and reads the contents in chunks. If you are able to write a version which retrieves the file data without opening a file, it *may* be faster.

Exactly which methods you should implement depends on how and where the data is stored. For network filesystems, a good candidate to implement, is the ``scandir`` methods which would otherwise call a combination of ``listdir`` and ``getinfo`` for each file.

In the general case, it is a good idea to look at how these methods are implemented in :class:`fs.base.FS`, and only write a custom version if it would be more efficient than the default.

* :meth:`fs.base.FS.appendbytes`
* :meth:`fs.base.FS.appendtext`
* :meth:`fs.base.FS.close`
* :meth:`fs.base.FS.copy`
* :meth:`fs.base.FS.copydir`
* :meth:`fs.base.FS.create`
* :meth:`fs.base.FS.desc`
* :meth:`fs.base.FS.exists`
* :meth:`fs.base.FS.filterdir`
* :meth:`fs.base.FS.getbytes`
* :meth:`fs.base.FS.gettext`
* :meth:`fs.base.FS.getmeta`
* :meth:`fs.base.FS.getsize`
* :meth:`fs.base.FS.getsyspath`
* :meth:`fs.base.FS.gettype`
* :meth:`fs.base.FS.geturl`
* :meth:`fs.base.FS.hassyspath`
* :meth:`fs.base.FS.hasurl`
* :meth:`fs.base.FS.isclosed`
* :meth:`fs.base.FS.isempty`
* :meth:`fs.base.FS.isfile`
* :meth:`fs.base.FS.lock`
* :meth:`fs.base.FS.movedir`
* :meth:`fs.base.FS.makedirs`
* :meth:`fs.base.FS.move`
* :meth:`fs.base.FS.open`
* :meth:`fs.base.FS.opendir`
* :meth:`fs.base.FS.removetree`
* :meth:`fs.base.FS.scandir`
* :meth:`fs.base.FS.setbytes`
* :meth:`fs.base.FS.setbin`
* :meth:`fs.base.FS.setfile`
* :meth:`fs.base.FS.settimes`
* :meth:`fs.base.FS.settext`
* :meth:`fs.base.FS.touch`
* :meth:`fs.base.FS.validatepath`

.. _helper-methods:

Helper Methods
--------------

* :meth:`fs.base.FS.getbasic`
* :meth:`fs.base.FS.getdetails`
* :meth:`fs.base.FS.check`
* :meth:`fs.base.FS.match`
* :meth:`fs.base.FS.tree`
