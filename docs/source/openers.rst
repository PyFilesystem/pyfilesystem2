.. _fs-urls:

FS URLs
=======

PyFilesystem can open a filesystem via an *FS URL*, which is similar to a URL you might enter in to a browser. FS URLs are useful if you want to specify a filesystem dynamically, such as in a conf file or from the command line.

Format
------

FS URLs are formatted in the following way::

    <protocol>://<username>:<password>@<resource>

The components are as follows:

* ``<protocol>`` Identifies the type of filesystem to create. e.g. ``osfs``, ``ftp``.
* ``<username>`` Optional username.
* ``<password>`` Optional password.
* ``<resource>`` A *resource*, which may be a domain, path, or both.

Here are a few examples::

    osfs://~/projects
    osfs://c://system32
    ftp://ftp.example.org/pub
    mem://
    ftp://will:daffodil@ftp.example.org/private


If ``<type>`` is not specified then it is assumed to be an :class:`~fs.osfs.OSFS`, i.e. the following FS URLs are equivalent::

    osfs://~/projects
    ~/projects

.. note::
    The `username` and `passwords` fields may not contain a colon (``:``) or an ``@`` symbol. If you need these symbols they may be `percent encoded <https://en.wikipedia.org/wiki/Percent-encoding>`_.


URL Parameters
--------------

FS URLs may also be appended with a ``?`` symbol followed by a url-encoded query string. For example::

    myprotocol://example.org?key1=value1&key2

The query string would be decoded as ``{"key1": "value1", "key2": ""}``.

Query strings are used to provide additional filesystem-specific information used when opening. See the filesystem documentation for information on what query string parameters are supported.


Opening FS URLS
---------------

To open a filesysem with a FS URL, you can use :meth:`~fs.opener.registry.Registry.open_fs`, which may be imported and used as follows::

    from fs import open_fs
    projects_fs = open_fs('osfs://~/projects')


Manually registering Openers
----------------------------

The ``fs.opener`` registry uses an entry point to install external openers
(see :ref:`extension`), and it does so once, when you import `fs` for the first
time. In some rare cases where entry points are not available (for instance,
when running an embedded interpreter) or when extensions are installed *after*
the interpreter has started (for instance in a notebook, see
`PyFilesystem2#485 <https://github.com/PyFilesystem/pyfilesystem2/issues/485>`_).

However, a new opener can be installed manually at any time with the
`fs.opener.registry.install` method. For instance, here's how the opener for
the `s3fs <https://github.com/PyFilesystem/s3fs>`_ extension can be added to
the registry::

    import fs.opener
    from fs_s3fs.opener import S3FSOpener

    fs.opener.registry.install(S3FSOpener)
    # fs.open_fs("s3fs://...") should now work
