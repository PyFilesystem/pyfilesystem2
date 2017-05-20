.. _extension:

Creating an extension
=====================

Once an new filesystem implemented, it is possible to distribute as a
subpackage contained in the ``fs`` namespace. Let's say you are trying
to create an extension for a filesystem called **AwesomeFS**.


Name
----

For the sake of clarity, and to give a clearer sight of the
Pyfilesystem2 ecosystem, your extension should be called **fs.awesome**
or **fs.awesomefs**, since PyPI allows packages to be namespaced. Let us
stick with **fs.awesome** for now.


Structure
---------

The extension must have either of the following structures: ::

  └── fs.awesome                            └── fs.awesome
      ├── fs                                    ├── fs
      │   ├── awesomefs.py                      │   ├── awesomefs
      │   └── opener                            |   |   ├── __init__.py
      │       └── awesomefs.py                  |   |   ├── some_file.py
      └── setup.py                              |   |   └── some_other_file.py
                                                │   └── opener
                                                │       └── awesomefs.py
                                                └── setup.py


The structure on the left will work fine if you only need a single file
to implement **AwesomeFS**, but if you end up creating more,
you should probably use the structure on the right (create a package
instead of a single file).

.. warning ::

   Do **NOT** create ``fs/__init__.py`` or ``fs/opener/__init__.py`` ! Since
   those files are vital to the main Pyfilesystem2 package, including them
   could result in having your extension break the whole Pyfilesystem2
   package when installing.


``setup.py``
------------

Refer to the `setuptools documentation <https://setuptools.readthedocs.io/>`_
to see how to write a ``setup.py`` file. There are only a few things that
should be kept in mind when creating a Pyfilesystem2 extension. Make sure that:

* the name of the package is the *namespaced* name (**fs.awesome** with our
  example).
* ``fs``, ``fs.opener`` and ``fs.awesomefs`` packages are included. Since
  you can't create ``fs/__init__.py`` and ``fs/opener/__init__.py``, setuptools
  won't be able to find your packages if you use ``setuptools.find_packages``,
  so you will have to include packages manually.
* ``fs`` is in the ``install_requires`` list, in order to
  always have Pyfilesystem2 installed before your extension.


Opener
------

To ensure your new filesystem can be reached through the generic ``fs.open_fs`` method,
you must declare a :class:`~fs.opener._base.Opener` in the ``fs/opener`` directory. With our example,
create a file called ``awesomefs.py`` containing the definition of ``AwesomeOpener``
or ``AwesomeFSOpener`` inside of the ``fs/opener`` directory. This will
allow your Filesystem to be created directly through ``fs.open_fs``, without
having to import your extension first !


Practices
---------

* Use relative imports whenever you try to access to a resource in the
  ``fs`` module or any of its submodules.
* Keep track of your achievements ! Add ``__version__``, ``__author__``,
  ``__author_email__`` and ``__license__`` variables to your project
  (either in ``fs/awesomefs.py`` or ``fs/awesomefs/__init__.py`` depending
  on the chosen structure), containing:

    ``__version__``
      the version of the extension (use `Semantic Versioning <http://semver.org/>`_ if possible !)

    ``__author__``
      your name(s)

    ``__author_email__``
      your email(s)

    ``__license__``
      the license of the subpackage


Example
-------

See `fs.sshfs <https://github.com/althonos/fs.sshfs>`_ for a functioning
PyFilesystem2 extension implementing the SFTP protocol.
