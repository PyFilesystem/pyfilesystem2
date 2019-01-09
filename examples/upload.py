"""
Upload a file to a server (or other filesystem)

Usage:

    python upload.py FILENAME <FS URL>

example:

    python upload.py foo.txt ftp://example.org/uploads/


"""

import os
import sys

from fs import open_fs

_, file_path, fs_url = sys.argv
filename = os.path.basename(file_path)

with open_fs(fs_url) as fs:
    if fs.exists(filename):
        print("destination exists! aborting.")
    else:
        with open(file_path, "rb") as bin_file:
            fs.upload(filename, bin_file)
print("upload successful!")
