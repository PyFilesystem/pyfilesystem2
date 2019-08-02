..  _info:

Resource Info
=============

Resource information (or *info*) describes standard file details such as
name, type, size, etc., and potentially other less-common information
associated with a file or directory.

You can retrieve resource info for a single resource by calling
:meth:`~fs.base.FS.getinfo`, or by calling  :meth:`~fs.base.FS.scandir`
which returns an iterator of resource information for the contents of
a directory. Additionally, :meth:`~fs.base.FS.filterdir` can filter the
resources in a directory by type and wildcard.

Here's an example of retrieving file information::

    >>> from fs.osfs import OSFS
    >>> fs = OSFS('.')
    >>> fs.writetext('example.txt', 'Hello, World!')
    >>> info = fs.getinfo('example.txt', namespaces=['details'])
    >>> info.name
    'example.txt'
    >>> info.is_dir
    False
    >>> info.size
    13

Info Objects
------------

PyFilesystem exposes the resource information via properties of
:class:`~fs.info.Info` objects.


Namespaces
----------

All resource information is contained within one of a number of
potential *namespaces*, which are logical key/value groups.

You can specify which namespace(s) you are interested in with the
`namespaces` argument to :meth:`~fs.base.FS.getinfo`. For example, the
following retrieves the ``details`` and ``access`` namespaces for a
file::

    resource_info = fs.getinfo('myfile.txt', namespaces=['details', 'access'])

In addition to the specified namespaces, the fileystem will also return
the ``basic`` namespace, which contains the name of the resource, and a
flag which indicates if the resource is a directory.

Basic Namespace
~~~~~~~~~~~~~~~

The ``basic`` namespace is always returned. It contains the following
keys:

=============== =================== ===========================================
Name            Type                Description
--------------- ------------------- -------------------------------------------
name            str                 Name of the resource.
is_dir          bool                A boolean that indicates if the resource
                                    is a directory.
=============== =================== ===========================================

The keys in this namespace can generally be retrieved very quickly. In
the case of :class:`~fs.osfs.OSFS` the namespace can be retrieved without
a potentially expensive system call.

Details Namespace
~~~~~~~~~~~~~~~~~

The ``details`` namespace contains the following keys.

================ =================== ==========================================
Name             type                Description
---------------- ------------------- ------------------------------------------
accessed         datetime            The time the file was last accessed.
created          datetime            The time the file was created.
metadata_changed datetime            The time of the last *metadata* (e.g.
                                     owner, group) change.
modified         datetime            The time file data was last changed.
size             int                 Number of bytes used to store the
                                     resource. In the case of files,
                                     this is the number of bytes in the
                                     file. For directories, the *size* is
                                     the overhead (in bytes) used to store
                                     the directory entry.
type             ResourceType        Resource type, one of the values
                                     defined in :class:`~fs.enums.ResourceType`.
================ =================== ==========================================

The time values (``accessed_time``, ``created_time`` etc.) may be
``None`` if the filesystem doesn't store that information. The ``size``
and ``type`` keys are guaranteed to be available, although ``type`` may
be :attr:`~fs.enums.ResourceType.unknown` if the filesystem is unable to
retrieve the resource type.

Access Namespace
~~~~~~~~~~~~~~~~

The ``access`` namespace reports permission and ownership information,
and contains the following keys.

================ =================== ==========================================
Name             type                Description
---------------- ------------------- ------------------------------------------
gid              int                 The group ID.
group            str                 The group name.
permissions      Permissions         An instance of
                                     :class:`~fs.permissions.Permissions`,
                                     which contains the permissions for the
                                     resource.
uid              int                 The user ID.
user             str                 The user name of the owner.
================ =================== ==========================================

This namespace is optional, as not all filesystems have a concept of
ownership or permissions. It is supported by :class:`~fs.osfs.OSFS`. Some
values may be ``None`` if they aren't supported by the filesystem.

Stat Namespace
~~~~~~~~~~~~~~

The ``stat`` namespace contains information reported by a call to
`os.stat <https://docs.python.org/3.5/library/stat.html>`_. This
namespace is supported by :class:`~fs.osfs.OSFS` and potentially other
filesystems which map directly to the OS filesystem. Most other
filesystems will not support this namespace.


LStat Namespace
~~~~~~~~~~~~~~~

The ``lstat`` namespace contains information reported by a call to
`os.lstat <https://docs.python.org/3.5/library/stat.html>`_. This
namespace is supported by :class:`~fs.osfs.OSFS` and potentially other
filesystems which map directly to the OS filesystem. Most other
filesystems will not support this namespace.

Link Namespace
~~~~~~~~~~~~~~

The ``link`` namespace contains information about a symlink.

=================== ======= ============================================
Name                type    Description
------------------- ------- --------------------------------------------
target              str     A path to the symlink target, or ``None`` if
                            this path is not a symlink.
                            Note, the meaning of this target is somewhat
                            filesystem dependent, and may not be a valid
                            path on the FS object.
=================== ======= ============================================

Other Namespaces
~~~~~~~~~~~~~~~~

Some filesystems may support other namespaces not covered here. See the
documentation for the specific filesystem for information on what
namespaces are supported.

You can retrieve such implementation specific resource information
with the :meth:`~fs.info.Info.get` method.

.. note::

    It is not an error to request a namespace (or namespaces) that the
    filesystem does *not* support. Any unknown namespaces will be
    ignored.

Missing Namespaces
------------------

Some attributes on the Info objects require that a given namespace be
present. If you attempt to reference them without the namespace being
present (because you didn't request it, or the filesystem doesn't
support it) then a :class:`~fs.errors.MissingInfoNamespace` exception
will be thrown. Here's how you might handle such exceptions::

    try:
        print('user is {}'.format(info.user))
    except errors.MissingInfoNamespace:
        # No 'access' namespace
        pass

If you prefer a *look before you leap* approach, you can use use the
:meth:`~fs.info.Info.has_namespace` method. Here's an example::


     if info.has_namespace('access'):
         print('user is {}'.format(info.user))

See :class:`~fs.info.Info` for details regarding info attributes.

Raw Info
--------

The :class:`~fs.info.Info` class is a wrapper around a simple data
structure containing the *raw* info. You can access this raw info with
the ``info.raw`` property.

.. note::

    The following is probably only of interest if you intend to
    implement a filesystem yourself.

Raw info data consists of a dictionary that maps the namespace name on
to a dictionary of information. Here's an example::

    {
        'access': {
            'group': 'staff',
            'permissions': ['g_r', 'o_r', 'u_r', 'u_w'],
            'user': 'will'
        },
        'basic': {
            'is_dir': False,
            'name': 'README.txt'
        },
        'details': {
            'accessed': 1474979730.0,
            'created': 1462266356.0,
            'metadata_changed': 1473071537.0,
            'modified': 1462266356.0,
            'size': 79,
            'type': 2
        }
    }


Raw resource information contains basic types only (strings, numbers,
lists, dict, None). This makes the resource information simple to
send over a network as it can be trivially serialized as JSON or other
data format.

Because of this requirement, times are stored as
`epoch times <https://en.wikipedia.org/wiki/Unix_time>`_. The Info object
will convert these to datetime objects from the standard library.
Additionally, the Info object will convert permissions from a list of
strings in to a :class:`~fs.permissions.Permissions` objects.

