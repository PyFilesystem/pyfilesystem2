"""
Remove all pyc files in a directory.

Usage:

    python rm_pyc.py <PATH or FS URL>

"""

import sys

from fs import open_fs


with open_fs(sys.argv[1]) as fs:
    count = fs.glob("**/*.pyc").remove()
print(f"{count} .pyc files remove")
