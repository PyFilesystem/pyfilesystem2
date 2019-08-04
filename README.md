# PyFilesystem2

Python's Filesystem abstraction layer.

[![PyPI version](https://badge.fury.io/py/fs.svg)](https://badge.fury.io/py/fs)
[![PyPI](https://img.shields.io/pypi/pyversions/fs.svg)](https://pypi.org/project/fs/)
[![Build Status](https://travis-ci.org/PyFilesystem/pyfilesystem2.svg?branch=master)](https://travis-ci.org/PyFilesystem/pyfilesystem2)
[![Windows Build Status](https://ci.appveyor.com/api/projects/status/github/pyfilesystem/pyfilesystem2?branch=master&svg=true)](https://ci.appveyor.com/project/willmcgugan/pyfilesystem2)
[![Coverage Status](https://coveralls.io/repos/github/PyFilesystem/pyfilesystem2/badge.svg)](https://coveralls.io/github/PyFilesystem/pyfilesystem2)
[![Codacy Badge](https://api.codacy.com/project/badge/Grade/30ad6445427349218425d93886ade9ee)](https://www.codacy.com/app/will-mcgugan/pyfilesystem2?utm_source=github.com&utm_medium=referral&utm_content=PyFilesystem/pyfilesystem2&utm_campaign=Badge_Grade)
[![Code Health](https://landscape.io/github/PyFilesystem/pyfilesystem2/master/landscape.svg?style=flat)](https://landscape.io/github/PyFilesystem/pyfilesystem2/master)

## Documentation

- [Wiki](https://www.pyfilesystem.org)
- [API Documentation](https://docs.pyfilesystem.org/)
- [GitHub Repository](https://github.com/PyFilesystem/pyfilesystem2)
- [Blog](https://www.willmcgugan.com/tag/fs/)

## Introduction

Think of PyFilesystem's `FS` objects as the next logical step to
Python's `file` objects. In the same way that file objects abstract a
single file, FS objects abstract an entire filesystem.

Let's look at a simple piece of code as an example. The following
function uses the PyFilesystem API to count the number of non-blank
lines of Python code in a directory. It works _recursively_, so it will
find `.py` files in all sub-directories.

```python
def count_python_loc(fs):
    """Count non-blank lines of Python code."""
    count = 0
    for path in fs.walk.files(filter=['*.py']):
        with fs.open(path) as python_file:
            count += sum(1 for line in python_file if line.strip())
    return count
```

We can call `count_python_loc` as follows:

```python
from fs import open_fs
projects_fs = open_fs('~/projects')
print(count_python_loc(projects_fs))
```

The line `project_fs = open_fs('~/projects')` opens an FS object that
maps to the `projects` directory in your home folder. That object is
used by `count_python_loc` when counting lines of code.

To count the lines of Python code in a _zip file_, we can make the
following change:

```python
projects_fs = open_fs('zip://projects.zip')
```

Or to count the Python lines on an FTP server:

```python
projects_fs = open_fs('ftp://ftp.example.org/projects')
```

No changes to `count_python_loc` are necessary, because PyFileystem
provides a simple consistent interface to anything that resembles a
collection of files and directories. Essentially, it allows you to write
code that is independent of where and how the files are physically
stored.

Contrast that with a version that purely uses the standard library:

```python
def count_py_loc(path):
    count = 0
    for root, dirs, files in os.walk(path):
        for name in files:
            if name.endswith('.py'):
                with open(os.path.join(root, name), 'rt') as python_file:
                    count += sum(1 for line in python_file if line.strip())
    return count
```

This version is similar to the PyFilesystem code above, but would only
work with the OS filesystem. Any other filesystem would require an
entirely different API, and you would likely have to re-implement the
directory walking functionality of `os.walk`.

## Credits

The following developers have contributed code and their time to this projects:

- [Will McGugan](https://github.com/willmcgugan)
- [Martin Larralde](https://github.com/althonos)
- [Giampaolo](https://github.com/gpcimino)
- [Geoff Jukes](https://github.com/geoffjukes)

See CONTRIBUTORS.md for a full list of contributors.

PyFilesystem2 owes a massive debt of gratitude to the following
developers who contributed code and ideas to the original version.

- Ryan Kelly
- Andrew Scheller
- Ben Timby

Apologies if I missed anyone, feel free to prompt me if your name is
missing here.

## Support

If commercial support is required, please contact [Will McGugan](mailto:willmcgugan@gmail.com).
