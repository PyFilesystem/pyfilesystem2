多文件系统
================

MultiFS是由一系列其他文件系统组成的文件系统，其中每个文件系统的目录结构覆盖序列中的先前文件系统。

这种文件系统的一个用途是选择性地覆盖一组文件，满足自定义的功能。 例如，创建一个可用于Web应用程序 *theme* 的文件系统。 我们从以下目录开始::

    `-- templates
        |-- snippets
        |   `-- panel.html
        |-- index.html
        |-- profile.html
        `-- base.html

    `-- theme
        |-- snippets
        |   |-- widget.html
        |   `-- extra.html
        |-- index.html
        `-- theme.html

我们想创建一个单独的文件系统，只有在 ``theme/`` 中没有找到时，才会从 ``templates/`` 加载一个文件。 我们可以这样做::

    from fs.osfs import OSFS
    from fs.multifs import MultiFS

    theme_fs = MultiFS()
    theme_fs.add_fs('templates', OSFS('templates'))
    theme_fs.add_fs('theme', OSFS('theme'))


现在我们有一个 ``theme_fs`` 文件系统，它提供了两个目录的单一视图::

    |-- snippets
    |   |-- panel.html
    |   |-- widget.html
    |   `-- extra.html
    |-- index.html
    |-- profile.html
    |-- base.html
    `-- theme.html


.. automodule:: fs.multifs
    :members:
