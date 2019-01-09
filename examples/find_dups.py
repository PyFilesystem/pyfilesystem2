"""
Find an print paths to files with identical contents.

Usage:

    python find_dups.py <PATH or FS URL>

"""

from collections import defaultdict
import hashlib
import sys

from fs import open_fs


def get_hash(bin_file):
    """Get the md5 hash of a file."""
    file_hash = hashlib.md5()
    while True:
        chunk = bin_file.read(1024 * 1024)
        if not chunk:
            break
        file_hash.update(chunk)
    return file_hash.hexdigest()


hashes = defaultdict(list)
with open_fs(sys.argv[1]) as fs:
    for path in fs.walk.files():
        with fs.open(path, "rb") as bin_file:
            file_hash = get_hash(bin_file)
        hashes[file_hash].append(path)

for paths in hashes.values():
    if len(paths) > 1:
        for path in paths[1:]:
            print(f" {path}")
        print()

