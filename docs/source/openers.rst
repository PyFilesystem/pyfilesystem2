.. _fs-urls:

FS URLs
=======

PyFilesystem can open filesystems via a FS URL, which are similar to the URLs you might enter in to a browser.

Using FS URLs can be useful if you want to be able to specify a filesystem dynamically, in a conf file (for instance).

FS URLs are parsed in to the following format::

    <type>://<username>:<password>@<resource>


The components are as follows:

* ``<type>`` Identifies the type of filesystem to create. e.g. ``osfs``, ``ftp``.
* ``<username>`` Optional username.
* ``<password>`` Optional password.
* ``<resource>`` A *resource*, which may be a domain, path, or both.

Here are a few examples::

    osfs://~/projects
    osfs://c://system32
    ftp://ftp.example.org/pub
    mem://

If ``<type>`` is not specified then it is assumed to be an :class:`~fs.osfs.OSFS`. The following FS URLs are equivalent::

    osfs://~/projects
    ~/projects

To open a filesysem with a FS URL, you can use :meth:`~fs.opener.Registry.open_fs`, which may be imported and used as follows::

    from fs import open_fs
    projects_fs = open_fs('osfs://~/projects')
