PyFilesystem2
=============

Python Filesystem abstraction layer.

[![PyPI version](https://badge.fury.io/py/fs.svg)](https://badge.fury.io/py/fs) [![PyPI](https://img.shields.io/pypi/pyversions/fs.svg)]() ![tests](https://travis-ci.org/PyFilesystem/pyfilesystem2.svg?branch=master) [![Coverage Status](https://coveralls.io/repos/github/PyFilesystem/pyfilesystem2/badge.svg)](https://coveralls.io/github/PyFilesystem/pyfilesystem2) [![Codacy Badge](https://api.codacy.com/project/badge/Grade/30ad6445427349218425d93886ade9ee)](https://www.codacy.com/app/will-mcgugan/pyfilesystem2?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=PyFilesystem/pyfilesystem2&amp;utm_campaign=Badge_Grade)

Think of PyFilesystem's ``FS`` objects as the next logical step to
Python's ``file`` objects. In the same way that file objects abstract a
single file, FS objects abstract an entire filesystem.

Let's look at a simple piece of code as an example. The following
function uses the PyFilesystem API to count the number of non-blank
lines of Python code in a directory. It works *recursively*, so it will
find ``.py`` files in all sub-directories.

```python
def count_python_loc(fs):
    """Count non-blank lines of Python code."""
    count = 0
    for path in fs.walk.files(filter=['*.py']):
        with fs.open(path) as python_file:
            count += sum(1 for line in python_file if line.strip())
    return count
```

We can call that function as follows::

```python
from fs import open_fs
projects_fs = open_fs('~/projects')
print(count_python_loc(projects_fs))
```

The line ``project_fs = open_fs('~/projects')`` opens an FS object that
maps to the ``projects`` directory in your home folder. That object is
used by ``count_python_loc`` when counting lines of code.

If we later want to count the lines of Python code in a zip file, then
we can make the following change::

```python
projects_fs = open_fs('zip://projects.zip')
```

No changes to ``count_python_loc`` are required, because PyFileystem
provides a simple consistent interface to anything that resembles a
collection of files and directories, including archives and network
filesystems.

Contrast that with a version that purely uses the standard library.

```python
def count_py_loc(path):
    count = 0
    for root, dirs, files in os.walk(path):
        for name in files:
            if name.endswith('.py'):
                with open(os.path.join(root, name)) as python_file:
                    count += sum(1 for line in python_file if line.strip())
```

The code is similar to the PyFilesystem version, but this code would
only work with the OS filesystem. Counting the lines of Python code in a
zip file would require a complete re-write since the API is quite
different. We would also have to re-implement the directory walking
provided by ``os.walk``