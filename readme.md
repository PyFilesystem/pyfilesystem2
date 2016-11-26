PyFilesystem2
=============

Python Filesystem abstraction layer

![tests](https://travis-ci.org/PyFilesystem/pyfilesystem2.svg?branch=master) [![Coverage Status](https://coveralls.io/repos/github/PyFilesystem/pyfilesystem2/badge.svg)](https://coveralls.io/github/PyFilesystem/pyfilesystem2)

Think of PyFilesystem's ``FS`` objects as the next logical step to
Python's ``file`` objects. In the same way that file objects abstract a
single file, FS objects abstract an entire filesystem.

Let's look at a simple piece of code as an example. The following function uses the PyFilesystem API to count the number of non-blank lines of Python code in a directory. It works *recursively*, so it will find ``.py`` files in all sub-directories.

```python
def count_python_loc(fs):
    """Count non-blank lines of Python code."""
    count = 0
    for path in fs.walk.files(filter=['*.py']):
        with fs.open(path) as python_file:
            for line in python_file:
                if line.strip():
                    count += 1
    return count
```

We can call that function as follows::

```python
from fs import open_fs
projects_fs = open_fs('~/projects')
print(count_python_loc(projects_fs))
```

The line ``project_fs = open_fs('~/projects')`` opens an FS object that maps to the ``projects`` directory in your home folder. That object is used by ``counts_python_loc`` when counting lines of code.

If we later want to count the lines of Python code in a zip file, then we can make the following change::

```python
projects_fs = open_fs('zip://projects.zip')
```

This works because PyFileystem provides a simple consistent interface to anything that resembles a collection of files and directories.

