指南
==============

PyFilesytem 接口简化了处理文件和目录的大多数方面。本指南涵盖了使用 FS 对象所需的知识。

为什么要使用PyFilesystem？
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

如果你很习惯使用Python标准库，你可能会想： *为什么要学习另一个API来处理文件？*

PyFilesystem API通常比 ``os`` 和 ``io`` 模块更简单 - 有更少的边缘情况和更少的方法来拍摄自己在脚。这可能是使用它的原因，但还有其他令人信服的理由，你应该使用 ``import fs`` 甚至直接的文件系统代码。

FS对象提供的抽象意味着您可以编写与您的文件物 理位置无关的代码。例如，如果您编写了一个函数来搜索目录中的重复文件，它将在硬盘驱动器上的目录，zip文件，FTP服务器，Amazon S3等上正常工作。

只要所选文件系统（或类似于文件系统的任何数据存储）存在FS对象，就可以使用相同的API。这意味着您可以将有关将数据存储在何处的决定推迟到以后。如果你决定将配置存储在 *cloud* 中，它可能是一个单行更改，而不是主要的重构。

PyFilesystem也可以有益于单元测试; 通过将OS文件系统与内存文件系统交换，您可以编写测试而无需管理（或模拟）文件IO。 您可以确保您的代码将在Linux，MacOS和Windows上工作。

打开文件系统
~~~~~~~~~~~~~~~~~~~

有两种方法可以打开文件系统。 第一种也是最自然的方法是导入合适的文件系统类并构造它。

下面是如何打开一个 :class:`~fs.osfs.OSFS` （操作系统文件系统），它映射到硬盘驱动器的文件和目录::

    >>> from fs.osfs import OSFS
    >>> home_fs = OSFS("~/")

这构造了一个FS对象，它管理给定系统路径下的文件和目录。 在这种情况下， ```〜/'`` ，这是你的主目录的快捷方式。

下面是如何列出主目录中的文件/目录::

    >>> home_fs.listdir('/')
    ['world domination.doc', 'paella-recipe.txt', 'jokes.txt', 'projects']

请注意， ``listdir`` 的参数是一个单斜线，表示我们想要列出文件系统的 *root* 。 这是因为从 ``home_fs`` 的角度来看，根目录是我们用来构建 ``OSFS`` 的目录。

还要注意，它是一个正斜杠，即使在Windows上。 这是因为FS路径以一致的格式而与平台无关。 诸如分隔符和编码的细节被抽象化。 有关详细信息，请参阅 :ref:`paths` 。
其他文件系统接口可能对其构造函数有其他要求。 例如，这里是如何打开一个FTP文件系统::

    >>> from ftpfs import FTPFS
    >>> debian_fs = FTPFS('ftp.mirror.nl')
    >>> debian_fs.listdir('/')
    ['debian-archive', 'debian-backports', 'debian', 'pub', 'robots.txt']

打开文件系统对象的第二种更通用的方法是通过 *opener* ，它从类似URL的语法中打开文件系统。 这里有一个替代方法来打开你的主目录::

    >>> from fs import open_fs
    >>> home_fs = open_fs('osfs://~/')
    >>> home_fs.listdir('/')
    ['world domination.doc', 'paella-recipe.txt', 'jokes.txt', 'projects']

当您想要将应用程序文件的物理位置存储在配置文件中时，*opener* 系统特别有用。

如果不在FS URL中指定协议，那么PyFilesystem将假设您想要从当前工作目录获得OSFS相对路径。 所以下面是一个等效的打开你的主目录的方法::

    >>> from fs import open_fs
    >>> home_fs = open_fs('.')
    >>> home_fs.listdir('/')
    ['world domination.doc', 'paella-recipe.txt', 'jokes.txt', 'projects']

树结构打印
~~~~~~~~~~~~~

调用FS对象上的 :meth:`~fs.base.FS.tree` 将打印文件系统的ascii树视图。 下面是一个例子::

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

这是一个有用的调试助手！


关闭
~~~~~~~

FS对象有一个 :meth:`~fs.base.FS.close` 方法，它将执行任何所需的清除操作。 对于许多文件系统（值得注意的是 :class:`~fs.osfs.OSFS` ），``close`` 方法很少。 其他文件系统只有在调用 ``close()`` 时才能完成文件或释放资源。

一旦使用完文件系统，你可以显式地调用 ``close`` 。 例如::

    >>> home_fs = open_fs('osfs://~/')
    >>> home_fs.settext('reminder.txt', 'buy coffee')
    >>> home_fs.close()

如果使用FS对象作为上下文管理器，将自动调用 ``close`` 。 以下等同于前面的示例::

    >>> with open_fs('osfs://~/') as home_fs:
    ...    home_fs.settext('reminder.txt', 'buy coffee')

建议使用FS对象作为上下文管理器，因为它将确保每个FS都关闭。

目录信息
~~~~~~~~~~~~~~~~~~~~~

文件系统对象有一个 :meth:`~fs.base.FS.listdir` 方法，类似于 ``os.listdir`` ; 它需要一个目录的路径并返回文件名列表。 下面是一个例子::

    >>> home_fs.listdir('/projects')
    ['fs', 'moya', 'README.md']

存在列出目录的替代方法; :meth:`~fs.base.FS.scandir` 返回一个 *iterable* 的 :ref:`info` 对象。 这里有一个例子::

    >>> directory = list(home_fs.scandir('/projects'))
    >>> directory
    [<dir 'fs'>, <dir 'moya'>, <file 'README.md'>]

信息对象比文件名具有许多优点。 例如，你可以知道 info 对象是否引用一个文件或一个目录 :attr:`~fs.info.Info.is_dir` 属性，而不需要额外的系统调用。 如果在 ``namespaces`` 参数中请求它，Info对象也可能包含诸如大小，修改时间等信息。


.. note::

    ``scandir`` 返回一个可迭代而不是一个列表的原因是，如果目录非常大，或者如果必须通过网络检索信息，那么在块中检索目录信息可能更有效。

此外，FS对象有一个 :meth:`~fs.base.FS.filterdir` 方法扩展 ``scandir`` ，能够通过通配符过滤目录内容。 以下是如何在目录中找到所有Python文件的方法::

    >>> code_fs = OSFS('~/projects/src')
    >>> directory = list(code_fs.filterdir('/', files=['*.py']))

默认情况下，``scandir`` 和 ``listdir`` 返回的资源信息对象只包含文件名和 ``is_dir`` 标志。您可以使用 ``namespaces`` 参数请求其他信息。以下是如何请求其他详细信息（例如文件大小和文件修改时间）::

    >>> directory = code_fs.filterdir('/', files=['*.py'], namespaces=['details'])

这将向资源信息对象添加一个``size`` 和 ``modified`` 属性（和其他）。这使得像这样的代码::

    >>> sum(info.size for info in directory)

有关详细信息，请参阅 :ref:`info` 。

子目录
~~~~~~~~~~~~~~~

PyFilesystem没有 *当前工作目录* 的概念，所以你不会在FS对象上找到一个 ``chdir`` 方法。幸运的是你不会错过它;使用子目录是一个微风与PyFilesystem。

您可以随时使用接受路径的方法指定目录。例如， ``home_fs.listdir（'/ projects'）`` 会获得 `projects` 目录的目录列表。或者，您可以调用 :meth:`~fs.base.FS.opendir` ，它为子目录返回一个新的FS对象。

例如，以下是如何列出主目录中的`projects`文件夹的目录内容::

    >>> home_fs = open_fs('~/')
    >>> projects_fs = home_fs.opendir('/projects')
    >>> projects_fs.listdir('/')
    ['fs', 'moya', 'README.md']

当你调用 ``opendir`` 时，FS对象返回一个 :class:`~fs.subfs.SubFS` 的实例。 如果你调用一个 ``SubFS`` 对象的任何方法，它就好像你在父文件系统上调用了相对于子目录的路径相同的方法。 :class:`~fs.base.FS.makedir` 和 :class:`~fs.base.FS.makedirs` 方法也为新创建的目录返回 ``SubFS`` 对象。 下面是如何在 ``~/projects`` 中创建一个新目录，并用几个文件初始化::

    >>> home_fs = open_fs('~/')
    >>> game_fs = home_fs.makedirs('projects/game')
    >>> game_fs.touch('__init__.py')
    >>> game_fs.settext('README.md', "Tetris clone")
    >>> game_fs.listdir('/')
    ['__init__.py', 'README.md']

使用 ``SubFS`` 对象意味着你通常可以避免编写很多路径处理代码，这往往容易出错。

使用文件
~~~~~~~~~~~~~~~~~~

您可以从FS对象打开一个文件 :meth:`~fs.base.FS.open` ，这与标准库中的 `io.open` 非常相似。 以下是如何在主目录中打开一个名为 ``reminder.txt`` 的文件::

    >>> with open_fs('~/') as home_fs:
    ...     with home_fs.open('reminder.txt') as reminder_file:
    ...        print(reminder_file.read())
    buy coffee

在 ``OSFS`` 的情况下，将返回标准的类文件对象。 其他文件系统可以返回支持相同方法的不同对象。 例如 :class:`~fs.memoryfs.MemoryFS` 将返回一个 ``io.BytesIO`` 对象。

PyFilesystem还提供了许多常见文件相关操作的快捷方式。 例如 :meth:`~fs.base.FS.getbytes` 将以字节形式返回文件内容，而且 :class:`~fs.base.FS.gettext` 将读取unicode文本。 这些方法通常优于明确打开文件，因为FS对象可能具有优化的实现。

其他 *快捷方式* 是 :meth:`~fs.base.FS.setbin` ， :meth:`~fs.base.FS.setbytes` ， :meth:`~fs.base.FS.settext` 。

Walking
~~~~~~~

通常，您将需要扫描给定目录中的文件和任何子目录。 这被称为 *walking* 文件系统。

以下是如何打印主目录中所有Python文件的路径::

    >>> from fs import open_fs
    >>> home_fs = open_fs('~/')
    >>> for path in home_fs.walk.files(filter=['*.py']):
    ...     print(path)

FS对象的 ``walk`` 属性是一个 :class:`~fs.walk.BoundWalker` 的实例，它应该能够处理大多数目录漫游需求。

参见 :ref:`walking` 有关walk目录的更多信息。

移动和复制
~~~~~~~~~~~~~~~~~~

您可以使用 :meth:`~fs.base.FS.move` 和 :meth:`~fs.base.FS.copy` 方法移动和复制文件内容，并且等效 :meth:`~fs.base.FS .movedir` 和 :meth:`~fs.base.FS.copydir` 方法对目录而不是文件进行操作。

这些移动和复制方法在可能的情况下被优化，并且取决于实现，它们可以比读取和写入文件更高性能。

要在 *文件系统之间移动和/或复制文件* （使用同一个文件系统），请使用 :mod:`~fs.move` 和 :mod:`~fs.copy` 模块。 这些模块中的方法接受FS对象和FS URLS。 例如，以下将压缩项目文件夹的内容::

    >>> from fs.copy import copy_fs
    >>> copy_fs('~/projects', 'zip://projects.zip')

这相当于下面这个例子，更冗长，代码::

    >>> from fs.copy import copy_fs
    >>> from fs.osfs import OSFS
    >>> from fs.zipfs import ZipFS
    >>> copy_fs(OSFS('~/projects'), ZipFS('projects.zip'))

:func:`~fs.copy.copy_fs` 和 :func:`~fs.copy.copy_dir` 函数也接受 :class:`~fs.walk.Walker` 参数，可以用来过滤将被复制的文件。 例如，如果你只想备份你的python文件，你可以使用像这样::

    >>> from fs.copy import copy_fs
    >>> from fs.walk import Walker
    >>> copy_fs('~/projects', 'zip://projects.zip', walker=Walker(files=['*.py']))
