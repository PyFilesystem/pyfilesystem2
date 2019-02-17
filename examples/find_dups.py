"""
Find paths to files with identical contents.

Usage:

    python find_dups.py <PATH or FS URL>

"""

from collections import defaultdict
import sys

from fs import open_fs


hashes = defaultdict(list)
with open_fs(sys.argv[1]) as fs:
    for path in fs.walk.files():
        file_hash = fs.hash(path, "md5")
        hashes[file_hash].append(path)

for paths in hashes.values():
    if len(paths) > 1:
        for path in paths:
            print(path)
        print()

