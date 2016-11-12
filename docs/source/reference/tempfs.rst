Temporary Filesystem
====================

A temporary filesytem is stored in a location defined by your OS (``/tmp`` on linux). The contents are deleted when the filesystem is closed.

A ``TempFS`` is a good way of preparing a directory structure in advance, that you can later copy. It can also be used as a temporary data store.

.. automodule:: fs.tempfs
    :members: