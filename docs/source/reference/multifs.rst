Multi Filesystem
================

A MultiFS is a filesystem composed of a sequence of other filesystems,
where the directory structure of each overlays the previous filesystem
in the sequence.

One use for such a filesystem would be to selectively override a set of
files, to customize behavior. For example, to create a filesystem that
could be used to *theme* a web application. We start with the following
directories::


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

And we want to create a single filesystem that will load a file from
``templates/`` only if it isn't found in ``theme/``. Here's how we could
do that::


    from fs.osfs import OSFS
    from fs.multifs import MultiFS

    theme_fs = MultiFS()
    theme_fs.add_fs('templates', OSFS('templates'))
    theme_fs.add_fs('theme', OSFS('theme'))


Now we have a ``theme_fs`` filesystem that presents a single view of both
directories::

    |-- snippets
    |   |-- panel.html
    |   |-- widget.html
    |   `-- extra.html
    |-- index.html
    |-- profile.html
    |-- base.html
    `-- theme.html


.. autoclass:: fs.multifs.MultiFS
    :members:
