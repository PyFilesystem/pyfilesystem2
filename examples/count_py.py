"""
Display how much storage is used in your Python files.

Usage:
    python count_py.py <PATH or FS URL>

"""

import sys

from fs import open_fs
from fs.filesize import traditional


fs_url = sys.argv[1]
count = 0

with open_fs(fs_url) as fs:
    for _path, info in fs.walk.info(filter=["*.py"], namespaces=["details"]):
        count += info.size

print(f'There is {traditional(count)} of Python in "{fs_url}"')
