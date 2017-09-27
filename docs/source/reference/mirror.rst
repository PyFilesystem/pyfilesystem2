fs.mirror
=========

Create a duplicate of a filesystem.

Mirroring will create a copy of a source filesystem on a destination
filesystem. If there are no files on the destination, then mirroring
is simply a straight copy. If there are any files or directories on the
destination they may be deleted or modified to match the source.

In order to avoid redundant copying of files, ``mirror`` can compare
timestamps, and only copy files with a newer modified date. This
timestamp comparison is only done if the file sizes are different.

This scheme will work if you have mirrored a directory previously, and
you would like to copy any changes. Otherwise you should set the
``copy_if_newer`` parameter to ``False`` to guarantee an exact copy, at
the expense of potentially copying extra files.

.. autofunction:: fs.mirror.mirror
