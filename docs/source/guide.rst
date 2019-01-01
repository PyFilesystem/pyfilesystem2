Guide
=====

The PyFilesytem interface simplifies most aspects of working with files and directories. This guide covers what you need to know about working with FS objects.

Why use PyFilesystem?
~~~~~~~~~~~~~~~~~~~~~

If you are comfortable using the Python standard library, you may be wondering; *why learn another API for working with files?*

The :ref:`interface` is generally simpler than the ``os`` and ``io`` modules -- there are fewer edge cases and less ways to shoot yourself in the foot. This may be reason alone to use it, but there are other compelling reasons you should use ``import fs`` for even straightforward filesystem code.

The abstraction offered by FS objects means that you can write code that is agnostic to where your files are physically located. For instance, if you wrote a function that searches a directory for duplicates files, it will work unaltered with a directory on your hard-drive, or in a zip file, on an FTP server, on Amazon S3, etc.

As long as an FS object exists for your chosen filesystem (or any data store that resembles a filesystem), you can use the same API. This means that you can defer the decision regarding where you store data to later. If you decide to store configuration in the *cloud*, it could be a single line change and not a major refactor.


PyFilesystem can also be beneficial for unit-testing; by swapping the OS filesystem with an in-memory filesystem, you can write tests without having to manage (or mock) file IO. And you can be sure that your code will work on Linux, MacOS, and Windows.

Opening Filesystems
~~~~~~~~~~~~~~~~~~~

There are two ways you can open a filesystem. The first and most natural way is to import the appropriate filesystem class and construct it.

Here's how you would open a :class:`~fs.osfs.OSFS` (Operating System File System), which maps to the files and directories of your hard-drive::

    >>> from fs.osfs import OSFS
    >>> home_fs = OSFS("~/")

This constructs an FS object which manages the files and directories under a given system path. In this case, ``'~/'``, which is a shortcut for your home directory.

Here's how you would list the files/directories in your home directory::

    >>> home_fs.listdir('/')
    ['world domination.doc', 'paella-recipe.txt', 'jokes.txt', 'projects']

Notice that the parameter to ``listdir`` is a single forward slash, indicating that we want to list the *root* of the filesystem. This is because from the point of view of ``home_fs``, the root is the directory we used to construct the ``OSFS``.

Also note that it is a forward slash, even on Windows. This is because FS paths are in a consistent format regardless of the platform. Details such as the separator and encoding are abstracted away. See :ref:`paths` for details.

Other filesystems interfaces may have other requirements for their constructor. For instance, here is how you would open a FTP filesystem::

    >>> from ftpfs import FTPFS
    >>> debian_fs = FTPFS('ftp.mirror.nl')
    >>> debian_fs.listdir('/')
    ['debian-archive', 'debian-backports', 'debian', 'pub', 'robots.txt']

The second, and more general way of opening filesystems objects, is via an *opener* which opens a filesystem from a URL-like syntax. Here's an alternative way of opening your home directory::

    >>> from fs import open_fs
    >>> home_fs = open_fs('osfs://~/')
    >>> home_fs.listdir('/')
    ['world domination.doc', 'paella-recipe.txt', 'jokes.txt', 'projects']

The opener system is particularly useful when you want to store the physical location of your application's files in a configuration file.

If you don't specify the protocol in the FS URL, then PyFilesystem will assume you want a OSFS relative from the current working directory. So the following would be an equivalent way of opening your home directory::

    >>> from fs import open_fs
    >>> home_fs = open_fs('.')
    >>> home_fs.listdir('/')
    ['world domination.doc', 'paella-recipe.txt', 'jokes.txt', 'projects']

Tree Printing
~~~~~~~~~~~~~

Calling :meth:`~fs.base.FS.tree` on a FS object will print an ascii tree view of your filesystem. Here's an example::

    >>> from fs import open_fs
    >>> my_fs = open_fs('.')
    >>> my_fs.tree()
    ├── locale
    │   └── readme.txt
    ├── logic
    │   ├── content.xml
    │   ├── data.xml
    │   ├── mountpoints.xml
    │   └── readme.txt
    ├── lib.ini
    └── readme.txt

This can be a useful debugging aid!


Closing
~~~~~~~

FS objects have a :meth:`~fs.base.FS.close` methd which will perform any required clean-up actions. For many filesystems (notably :class:`~fs.osfs.OSFS`), the ``close`` method does very little. Other filesystems may only finalize files or release resources once ``close()`` is called.

You can call ``close`` explicitly once you are finished using a filesystem. For example::

    >>> home_fs = open_fs('osfs://~/')
    >>> home_fs.writetext('reminder.txt', 'buy coffee')
    >>> home_fs.close()

If you use FS objects as a context manager, ``close`` will be called automatically. The following is equivalent to the previous example::

    >>> with open_fs('osfs://~/') as home_fs:
    ...    home_fs.writetext('reminder.txt', 'buy coffee')

Using FS objects as a context manager is recommended as it will ensure every FS is closed.

Directory Information
~~~~~~~~~~~~~~~~~~~~~

Filesystem objects have a :meth:`~fs.base.FS.listdir` method which is similar to ``os.listdir``; it takes a path to a directory and returns a list of file names. Here's an example::

    >>> home_fs.listdir('/projects')
    ['fs', 'moya', 'README.md']

An alternative method exists for listing directories; :meth:`~fs.base.FS.scandir` returns an *iterable* of :ref:`info` objects. Here's an example::

    >>> directory = list(home_fs.scandir('/projects'))
    >>> directory
    [<dir 'fs'>, <dir 'moya'>, <file 'README.md'>]

Info objects have a number of advantages over just a filename. For instance you can tell if an info object references a file or a directory with the :attr:`~fs.info.Info.is_dir` attribute, without an additional system call. Info objects may also contain information such as size, modified time, etc. if you request it in the ``namespaces`` parameter.


.. note::

    The reason that ``scandir`` returns an iterable rather than a list, is that it can be more efficient to retrieve directory information in chunks if the directory is very large, or if the information must be retrieved over a network.

Additionally, FS objects have a :meth:`~fs.base.FS.filterdir` method which extends ``scandir`` with the ability to filter directory contents by wildcard(s). Here's how you might find all the Python files in a directory:

    >>> code_fs = OSFS('~/projects/src')
    >>> directory = list(code_fs.filterdir('/', files=['*.py']))

By default, the resource information objects returned by ``scandir`` and ``listdir`` will contain only the file name and the ``is_dir`` flag. You can request additional information with the ``namespaces`` parameter. Here's how you can request additional details (such as file size and file modified times)::

    >>> directory = code_fs.filterdir('/', files=['*.py'], namespaces=['details'])

This will add a ``size`` and ``modified`` property (and others) to the resource info objects. Which makes code such as this work::

    >>> sum(info.size for info in directory)

See :ref:`info` for more information.

Sub Directories
~~~~~~~~~~~~~~~

PyFilesystem has no notion of a *current working directory*, so you won't find a ``chdir`` method on FS objects. Fortunately you won't miss it; working with sub-directories is a breeze with PyFilesystem.

You can always specify a directory with methods which accept a path. For instance, ``home_fs.listdir('/projects')`` would get the directory listing for the `projects` directory. Alternatively, you can call :meth:`~fs.base.FS.opendir` which returns a new FS object for the sub-directory.

For example, here's how you could list the directory contents of a `projects` folder in your home directory::


    >>> home_fs = open_fs('~/')
    >>> projects_fs = home_fs.opendir('/projects')
    >>> projects_fs.listdir('/')
    ['fs', 'moya', 'README.md']

When you call ``opendir``, the FS object returns an instance of a :class:`~fs.subfs.SubFS`. If you call any of the methods on a ``SubFS`` object, it will be as though you called the same method on the parent filesystem with a path relative to the sub-directory.

The :class:`~fs.base.FS.makedir` and :class:`~fs.base.FS.makedirs` methods also return ``SubFS`` objects for the newly create directory. Here's how you might create a new directory in ``~/projects`` and initialize it with a couple of files::

    >>> home_fs = open_fs('~/')
    >>> game_fs = home_fs.makedirs('projects/game')
    >>> game_fs.touch('__init__.py')
    >>> game_fs.writetext('README.md', "Tetris clone")
    >>> game_fs.listdir('/')
    ['__init__.py', 'README.md']

Working with ``SubFS`` objects means that you can generally avoid writing much path manipulation code, which tends to be error prone.

Working with Files
~~~~~~~~~~~~~~~~~~

You can open a file from a FS object with :meth:`~fs.base.FS.open`, which is very similar to ``io.open`` in the standard library. Here's how you might open a file called "reminder.txt" in your home directory::

    >>> with open_fs('~/') as home_fs:
    ...     with home_fs.open('reminder.txt') as reminder_file:
    ...        print(reminder_file.read())
    buy coffee

In the case of a ``OSFS``, a standard file-like object will be returned. Other filesystems may return a different object supporting the same methods. For instance, :class:`~fs.memoryfs.MemoryFS` will return a ``io.BytesIO`` object.

PyFilesystem also offers a number of shortcuts for common file related operations. For instance, :meth:`~fs.base.FS.readbytes` will return the file contents as a bytes, and :meth:`~fs.base.FS.readtext` will read unicode text. These methods is generally preferable to explicitly opening files, as the FS object may have an optimized implementation.

Other *shortcut* methods are :meth:`~fs.base.FS.download`, :meth:`~fs.base.FS.upload`, :meth:`~fs.base.FS.writebytes`, :meth:`~fs.base.FS.writetext`.

Walking
~~~~~~~

Often you will need to scan the files in a given directory, and any sub-directories. This is known as *walking* the filesystem.

Here's how you would print the paths to all your Python files in your home directory::

    >>> from fs import open_fs
    >>> home_fs = open_fs('~/')
    >>> for path in home_fs.walk.files(filter=['*.py']):
    ...     print(path)

The ``walk`` attribute on FS objects is instance of a :class:`~fs.walk.BoundWalker`, which should be able to handle most directory walking requirements.

See :ref:`walking` for more information on walking directories.

Globbing
~~~~~~~~

Closely related to walking a filesystem is *globbing*, which is a slightly higher level way of scanning filesystems. Paths can be filtered by a *glob* pattern, which is similar to a wildcard (such as ``*.py``), but can match multiple levels of a directory structure.

Here's an example of globbing, which removes all the ``.pyc`` files in your project directory::

    >>> from fs import open_fs
    >>> open_fs('~/project').glob('**/*.pyc').remove()
    62

See :ref:`globbing` for more information.


Moving and Copying
~~~~~~~~~~~~~~~~~~

You can move and copy file contents with :meth:`~fs.base.FS.move` and :meth:`~fs.base.FS.copy` methods, and the equivalent :meth:`~fs.base.FS.movedir` and :meth:`~fs.base.FS.copydir` methods which operate on directories rather than files.

These move and copy methods are optimized where possible, and depending on the implementation, they may be more performant than reading and writing files.

To move and/or copy files *between* filesystems (as apposed to within the same filesystem), use the :mod:`~fs.move` and :mod:`~fs.copy` modules. The methods in these modules accept both FS objects and FS URLS. For instance, the following will compress the contents of your projects folder::

    >>> from fs.copy import copy_fs
    >>> copy_fs('~/projects', 'zip://projects.zip')

Which is the equivalent to this, more verbose, code::

    >>> from fs.copy import copy_fs
    >>> from fs.osfs import OSFS
    >>> from fs.zipfs import ZipFS
    >>> copy_fs(OSFS('~/projects'), ZipFS('projects.zip'))

The :func:`~fs.copy.copy_fs` and :func:`~fs.copy.copy_dir` functions also accept a :class:`~fs.walk.Walker` parameter, which can you use to filter the files that will be copied. For instance, if you only wanted back up your python files, you could use something like this::

    >>> from fs.copy import copy_fs
    >>> from fs.walk import Walker
    >>> copy_fs('~/projects', 'zip://projects.zip', walker=Walker(filter=['*.py']))

An alternative to copying is *mirroring*, which will copy a filesystem them keep it up to date by copying only changed files / directories. See :func:`~fs.mirror.mirror`.
