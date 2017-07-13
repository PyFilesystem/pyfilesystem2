.. _extension:

Creating an extension
=====================

Once an new filesystem implemented, it is possible to distribute as a
subpackage contained in the ``fs`` namespace. Let's say you are trying
to create an extension for a filesystem called **AwesomeFS**.


Naming Convention
-----------------

For the sake of clarity, and to give a clearer sight of the
Pyfilesystem2 ecosystem, your extension should be called **fs.awesome**
or **fs.awesomefs**, since PyPI allows packages to be namespaced. Let us
stick with **fs.awesome** for now.


Extension Structure
-------------------

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



Opener
------

In order for your filesystem to be opened through :doc:`openers` like the
other builtin filesystems, you must declare an :class:`~fs.opener.base.Opener`.
For good practice, the implementation should be done in a file inside the
``fs.opener`` module, so in our case, ``fs/opener/awesomefs.py``. Let us call
the opener ``AwesomeFSOpener``. Once done with the implementation, you must
declare the opener as an entry point in the setup file for ``fs.open_fs`` to
actually register this new protocol. See below for an example, or read about
`entry points <http://setuptools.readthedocs.io/en/latest/setuptools.html?highlight=entry%20points#dynamic-discovery-of-services-and-plugins>`_
if you want to know more.



The ``setup.py`` file
---------------------

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
* Ìf you created an opener, include it as an ``fs.opener`` entry point, using
  the name of the entry point as the protocol to be used. If the protocol to
  open ``AwesomeFS`` were ``awe://``, the entry point declaration would be::

      awe = fs.opener.awesomefs:AwesomeFS

  (format, like any other setuptools entry point, is ``protocol = module.submodule:OpenerClass``).


Here is an minimal ``setup.py`` for our project:

.. code:: python

   from setuptools import setup
   setup(
       author="You !",
       author_email="your.email@domain.ext",
       description="An awesome filesystem for pyfilesystem2 !",
       install_requires=["fs"],
       entry_points = {'fs.opener': [
           'awe = fs.opener.awesomefs:AwesomeFS',
       ]},
       license="MY LICENSE",
       name='fs.awesome',
       packages=['fs', 'fs.opener', 'fs.awesome'], # if fs.awesomefs is a package
       #packages=['fs', 'fs.opener'] # if fs.awesomefs is not a package
       version="X.Y.Z",
   )

Good Practices
--------------

* Use `relative imports <https://www.python.org/dev/peps/pep-0328/#guido-s-decision>`_
  whenever you try to access to a resource in the ``fs`` module or any of its
  submodules.
* Keep track of your achievements ! Add ``__version__``, ``__author__``,
  ``__author_email__`` and ``__license__`` variables to your project
  (either in ``fs/awesomefs.py`` or ``fs/awesomefs/__init__.py`` depending
  on the chosen structure), containing:

    ``__version__``
      the version of the extension (use `Semantic Versioning
      <http://semver.org/>`_ if possible !)

    ``__author__``
      your name(s)

    ``__author_email__``
      your email(s)

    ``__license__``
      the license of the subpackage


Live Example
------------

See `fs.sshfs <https://github.com/althonos/fs.sshfs>`_ for a functioning
PyFilesystem2 extension implementing a Pyfilesystem2 filesystem over SSH.
