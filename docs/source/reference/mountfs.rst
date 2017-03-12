Mount 文件系统
================

MountFS 是一个 *虚拟* 文件系统，可以无缝地将子目录映射到其他文件系统。

例如，我们有两个文件系统分别包含配置文件和资源::

   [config_fs]
   |-- config.cfg
   `-- defaults.cfg

   [resources_fs]
   |-- images
   |   |-- logo.jpg
   |   `-- photo.jpg
   `-- data.dat

我们可以将这些文件系统合并到单个文件系统中，使用以下代码::

    from fs.mountfs import MountFS
    combined_fs = MountFS()
    combined_fs.mount('config', config_fs)
    combined_fs.mount('resources', resources_fs)

这将创建一个文件系统，其中 ``config/`` 映射到 ``config_fs`` 的路径和 ``resources/`` 映射到 `resources_fs` 的路径::

    [combined_fs]
    |-- config
    |   |-- config.cfg
    |   `-- defaults.cfg
    `-- resources
        |-- images
        |   |-- logo.jpg
        |   `-- photo.jpg
        `-- data.dat

现在两个文件系统可以使用相同的路径结构访问::

    print(combined_fs.gettext('/config/defaults.cfg'))
    read_jpg(combined_fs.open('/resources/images/logo.jpg', 'rb')

.. automodule:: fs.mountfs
    :members:
