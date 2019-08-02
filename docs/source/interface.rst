.. _interface:

PyFilesystem API
----------------

The following is a complete list of methods on PyFilesystem objects.

* :meth:`~fs.base.FS.appendbytes` Append bytes to a file.
* :meth:`~fs.base.FS.appendtext` Append text to a file.
* :meth:`~fs.base.FS.check` Check if a filesystem is open or raise error.
* :meth:`~fs.base.FS.close` Close the filesystem.
* :meth:`~fs.base.FS.copy` Copy a file to another location.
* :meth:`~fs.base.FS.copydir` Copy a directory to another location.
* :meth:`~fs.base.FS.create` Create or truncate a file.
* :meth:`~fs.base.FS.desc` Get a description of a resource.
* :meth:`~fs.base.FS.download` Copy a file on the filesystem to a file-like object.
* :meth:`~fs.base.FS.exists` Check if a path exists.
* :meth:`~fs.base.FS.filterdir` Iterate resources, filtering by wildcard(s).
* :meth:`~fs.base.FS.getbasic` Get basic info namespace for a resource.
* :meth:`~fs.base.FS.getdetails` Get details info namespace for a resource.
* :meth:`~fs.base.FS.getinfo` Get info regarding a file or directory.
* :meth:`~fs.base.FS.getmeta` Get meta information for a resource.
* :meth:`~fs.base.FS.getospath` Get path with encoding expected by the OS.
* :meth:`~fs.base.FS.getsize` Get the size of a file.
* :meth:`~fs.base.FS.getsyspath` Get the system path of a resource, if one exists.
* :meth:`~fs.base.FS.gettype` Get the type of a resource.
* :meth:`~fs.base.FS.geturl` Get a URL to a resource, if one exists.
* :meth:`~fs.base.FS.hassyspath` Check if a resource maps to the OS filesystem.
* :meth:`~fs.base.FS.hash` Get the hash of a file's contents.
* :meth:`~fs.base.FS.hasurl` Check if a resource has a URL.
* :meth:`~fs.base.FS.isclosed` Check if the filesystem is closed.
* :meth:`~fs.base.FS.isempty` Check if a directory is empty.
* :meth:`~fs.base.FS.isdir` Check if path maps to a directory.
* :meth:`~fs.base.FS.isfile` Check if path maps to a file.
* :meth:`~fs.base.FS.islink` Check if path is a link.
* :meth:`~fs.base.FS.listdir` Get a list of resources in a directory.
* :meth:`~fs.base.FS.lock` Get a thread lock context manager.
* :meth:`~fs.base.FS.makedir` Make a directory.
* :meth:`~fs.base.FS.makedirs` Make a directory and intermediate directories.
* :meth:`~fs.base.FS.match` Match one or more wildcard patterns against a path.
* :meth:`~fs.base.FS.move` Move a file to another location.
* :meth:`~fs.base.FS.movedir` Move a directory to another location.
* :meth:`~fs.base.FS.open` Open a file on the filesystem.
* :meth:`~fs.base.FS.openbin` Open a binary file.
* :meth:`~fs.base.FS.opendir` Get a filesystem object for a directory.
* :meth:`~fs.base.FS.readbytes` Read file as bytes.
* :meth:`~fs.base.FS.readtext` Read file as text.
* :meth:`~fs.base.FS.remove` Remove a file.
* :meth:`~fs.base.FS.removedir` Remove a directory.
* :meth:`~fs.base.FS.removetree` Recursively remove file and directories.
* :meth:`~fs.base.FS.scandir` Scan files and directories.
* :meth:`~fs.base.FS.setinfo` Set resource information.
* :meth:`~fs.base.FS.settimes` Set modified times for a resource.
* :meth:`~fs.base.FS.touch` Create a file or update times.
* :meth:`~fs.base.FS.tree` Render a tree view of the filesystem.
* :meth:`~fs.base.FS.upload` Copy a binary file to the filesystem.
* :meth:`~fs.base.FS.validatepath` Check a path is valid and return normalized path.
* :meth:`~fs.base.FS.writebytes` Write a file as bytes.
* :meth:`~fs.base.FS.writefile` Write a file-like object to the filesystem.
* :meth:`~fs.base.FS.writetext` Write a file as text.
