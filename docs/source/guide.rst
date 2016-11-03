Guide
=====


Opening Filesystems
~~~~~~~~~~~~~~~~~~~

There are two ways you can open a filesystem. The first and most natural way is to import the appropriate filesystem class and construct it.

Here's how you would open a :class:`fs.osfs.OSFS` (Operating System File System), which maps to the files and directories on your hard-drive::

    >>> from fs.osfs import OSFS
    >>> home_fs = OSFS("~/")

The constructor takes a system path of the directory you wish to manage. The filesystem object may manage only those files and directories under that *root* directory.

Here's how you would list the files/directories in your home directory::

    >>> home_fs.listdir('/')
    ['world domination.doc', 'paella-recipe.txt', 'jokes.txt', 'projects']

Notice that the parameter to ``listdir`` is a single forward slash, indicating that we want to list the *root* of the filesystem. This is because from the point of view of ``home_fs``, the root is the directory we used to construct the ``OSFS``.

Also note that it is a forward slash, even on windows. This is because FS paths are in a consistent format regardless of the platform. Details such as the separator and encoding are abstracted away.

Other filesystems interfaces may have other requirements for their constructor. For instance, here is how you would open a FTP filesystem::

    >>> from ftpfs import FTPFS
    >>> debian_fs = FTPFS('ftp.mirror.nl')
    >>> debian_fs.listdir('/')
    ['debian-archive', 'debian-backports', 'debian', 'pub', 'robots.txt']

The second, and more general way of opening filesystems objects, is via an *opener* which opens a filesystem from a URL-like syntax. Here's an alternative way of opening our home directory::

    >>> from fs.opener import open_fs
    >>> home_fs = open_fs('osfs://~/')
    >>> home_fs.listdir('/')
    ['world domination.doc', 'paella-recipe.txt', 'jokes.txt', 'projects']

The opener system is particularly useful when you want to store the physical location of your application's files in a configuration file.

Listing Directories
~~~~~~~~~~~~~~~~~~~

Filesystem objects have a ``listdir`` method which is similar to ``os.listdir``; it takes a path to a directory and returns a list of file names. Here's an example::

    >>> home_fs.listdir('/projects')
    ['fs', 'moya', 'README.md']

An alternative method exists for listing directories; if you call :meth:`fs.base.FS.scandir` it will return a *generator* of :ref:`info` objects. Here's an example::

    >>> directory = list(home_fs.scandir('/projects'))
    >>> directory
    [<dir 'fs'>, <dir 'moya'>, <file 'README.md'>]

Info objects have a number of advantages over just a filename. For instance, you can know if a name references a directory with the :meth:`fs.info.Info.is_dir` method. Otherwise you would need to call :meth:`fs.base.FS.isdir`, which may involve an additional system call (or request in the case of a network filesystem).

The reason that ``scandir`` returns a *generator* rather than a list, is that it can be more efficient to retrieve directory information in chunks if the directory is very large, or if the information must be retrieved over a network.

Additionally, FS objects have a :meth:`fs.base.FS.filterdir` method which extends `scandir` with the ability to filter directory contents by wildcard(s). Here's how you might find all the Python code in a filesystem:

    >>> code_fs = OSFS('~/projects/src')
    >>> directory = list(code_fs.filterdir('/', wildcards=['*.py']))

Sub Directories
~~~~~~~~~~~~~~~

PyFilesystem has no notion of a *current working directory*, so you won't find a ``chdir`` method on FS objects. You can either specify the directory explicitly in a path argument, or call :meth:`fs.base.FS.opendir` which returns a new FS object for the resources under the sub-directory.

For example, here's how you could list the directory contents of a `projects` folder in your home directory::


    >>> home_fs = open_fs('~/')
    >>> projects_fs = home_fs.opendir('projects')
    >>> projects_fs.listdir('/')
    ['fs', 'moya', 'README.md']

When you call ``opendir``, the FS object returns an instance of a :class:`fs.subfs.SubFS`, which maps to the resources in a sub-directory. If you call any of the methods on a ``SubFS`` object, it will be as though you called the same method on the parent filesystem relative to the opened sub-directory.

The :class:`fs.base.FS.makedir` and :class:`fs.base.FS.makedirs` methods also return ``SubFS`` objects for the newly create directory. Here's how you might create a new directory in ``~/projects`` and initialize it with a couple of files::

    >>> home_fs = open_fs('~/')
    >>> game_fs = home_fs.makedirs('projects/game')
    >>> game_fs.touch('__init__.py')
    >>> game_fs.settext('README.md', "Tetris clone")
    >>> game_fs.listdir('/')
    ['__init__.py', 'README.md']


Opening Files
~~~~~~~~~~~~~

Opening a file on
