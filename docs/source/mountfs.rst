Mount FS
========

A Mount FS is a *virtual* filesystem which can seemlessly map sub-
directories on to other filesystems.

For example, lets say we have two filesystems containing config files
and resources respectively::

   [config_fs]
   |-- config.cfg
   `-- defaults.cfg

   [resources_fs]
   |-- images
   |   |-- logo.jpg
   |   `-- photo.jpg
   `-- data.dat

We can combine these filesystems in to a single filesystem with the
following code::

    from fs.mountfs import MountFS
    combined_fs = MountFS()
    combined_fs.mount('config', config_fs)
    combined_fs.mount('resources', resources_fs)

This will create a filesystem where paths under ``config/`` map to
``config_fs``, and paths under ``resources/`` map to ``resources_fs``::

    [combined_fs]
    |-- config
    |   |-- config.cfg
    |   `-- defaults.cfg
    `-- resources
        |-- images
        |   |-- logo.jpg
        |   `-- photo.jpg
        `-- data.dat

Now both filesystems may be accessed with the same path structure::

    print(combined_fs.gettext('/config/defaults.cfg'))
    read_jpg(combined_fs.open('/resources/images/logo.jpg', 'rb')

.. automodule:: fs.mountfs
    :members: