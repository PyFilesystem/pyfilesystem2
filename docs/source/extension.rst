.. _extension:

Creating an extension
=====================

Once a filesystem has been implemented, it can be integrated with other
applications and projects using PyFilesystem.


Naming Convention
-----------------

For visibility in PyPi, we recommend that your package be prefixed with
``fs-``. For instance if you have implemented an ``AwesomeFS``
PyFilesystem class, your packaged could be be named ``fs-awesome`` or
``fs-awesomefs``.


Opener
------

In order for your filesystem to be opened with an :ref:`FS URL <fs-urls>`
you should define an :class:`~fs.opener.base.Opener` class.

Here's an example taken from an Amazon S3 Filesystem::


  """Defines the S3FSOpener."""

  __all__ = ['S3FSOpener']

  from fs.opener import Opener
  from fs.opener.errors import OpenerError

  from ._s3fs import S3FS


  class S3FSOpener(Opener):
      protocols = ['s3']

      def open_fs(self, fs_url, parse_result, writeable, create, cwd):
          bucket_name, _, dir_path = parse_result.resource.partition('/')
          if not bucket_name:
              raise OpenerError(
                  "invalid bucket name in '{}'".format(fs_url)
              )
          s3fs = S3FS(
              bucket_name,
              dir_path=dir_path or '/',
              aws_access_key_id=parse_result.username or None,
              aws_secret_access_key=parse_result.password or None,
          )
          return s3fs

By convention this would be defined in ``opener.py``.


To register the opener you will need to define an `entry point
<http://setuptools.readthedocs.io/en/latest/setuptools.html?highlight=entry%20points#dynamic-discovery-of-services-and-plugins>`_
in your setup.py. See below for an example.


The setup.py file
-----------------

Refer to the `setuptools documentation <https://setuptools.readthedocs.io/>`_
to see how to write a ``setup.py`` file. There are only a few things that
should be kept in mind when creating a Pyfilesystem2 extension. Make sure that:

* ``fs`` is in the ``install_requires`` list. You should reference the
  version number with the ``~=`` operator which ensures that the install
  will get any bugfix releases of PyFilesystem but not any potentially
  breaking changes.
* Ìf you created an opener, include it as an ``fs.opener`` entry point,
  using the name of the entry point as the protocol to be used.

Here is an minimal ``setup.py`` for our project:

.. code:: python

   from setuptools import setup
   setup(
       name='fs-awesomefs',  # Name in PyPi
       author="You !",
       author_email="your.email@domain.ext",
       description="An awesome filesystem for pyfilesystem2 !",
       install_requires=[
           "fs~=2.0.5"
       ],
       entry_points = {
           'fs.opener': [
               'awe = awesomefs.opener:AwesomeFSOpener',
           ]
       },
       license="MY LICENSE",
       packages=['awesomefs'],
       version="X.Y.Z",
   )

Good Practices
--------------

Keep track of your achievements! Add the following values to your ``__init__.py``:

 * ``__version__`` The version of the extension (we recommend following
   `Semantic Versioning <http://semver.org/>`_),
 * ``__author__`` Your name(s).
 * ``__author_email__`` Your email(s).
 * ``__license__`` The module's license.

Let us Know
-----------

Contact us to add your filesystem to the `PyFilesystem Wiki <https://www.pyfilesystem.org/page/index-of-filesystems/>`_.


Live Example
------------

See `fs.sshfs <https://github.com/althonos/fs.sshfs>`_ for a functioning
PyFilesystem2 extension implementing a Pyfilesystem2 filesystem over
SSH.
