from __future__ import print_function
from __future__ import unicode_literals

import io
from io import SEEK_SET, SEEK_CUR

from .mode import Mode


class RawWrapper(object):
    """Convert a Python 2 style file-like object in to a IO object."""

    def __init__(self, f, mode=None, name=None):
        self._f = f
        self.is_io = isinstance(f, io.IOBase)
        self.mode = mode or getattr(f, 'mode', None)
        self.name = name
        self.closed = False
        super(RawWrapper, self).__init__()

    def close(self):
        self._f.close()
        self.closed = True

    def fileno(self):
        return self._f.fileno()

    def flush(self):
        return self._f.flush()

    def isatty(self):
        return self._f.isatty()

    def seek(self, offset, whence=SEEK_SET):
        return self._f.seek(offset, whence)

    def readable(self):
        return getattr(
            self._f,
            'readable',
            Mode(self.mode).reading
        )

    def writable(self):
        return getattr(
            self._f,
            'writable',
            Mode(self.mode).writing
        )

    def seekable(self):
        if self.is_io:
            return self._f.seekable()
        try:
            self.seek(0, SEEK_CUR)
        except IOError:
            return False
        else:
            return True

    def tell(self):
        return self._f.tell()

    def truncate(self, size=None):
        return self._f.truncate(size)

    def write(self, data):
        count = self._f.write(data)
        return len(data) if count is None else count

    def read(self, n=-1):
        if n == -1:
            return self.readall()
        return self._f.read(n)

    def read1(self, n=-1):
        if self.is_io:
            return self._f.read1(n)
        return self.read(n)

    def readall(self):
        return self._f.read()

    def readinto(self, b):
        if self.is_io:
            return self._f.readinto(b)
        data = self._f.read(len(b))
        bytes_read = len(data)
        b[:len(data)] = data
        return bytes_read

    def readline(self, limit=-1):
        return self._f.readline(limit)

    def readlines(self, hint=-1):
        return self._f.readlines(hint)

    def writelines(self, sequence):
        return self._f.writelines(sequence)

    def __enter__(self):
        return self

    def __exit__(self, *args, **kwargs):
        self.close()

    def __iter__(self):
        return iter(self._f)


def make_stream(name,
                bin_file,
                mode='r',
                buffering=-1,
                encoding=None,
                errors=None,
                newline=None,
                line_buffering=False,
                **kwargs):
    """Take a Python 2.x binary file and return an IO Stream."""
    reading = 'r' in mode
    writing = 'w' in mode
    appending = 'a' in mode
    binary = 'b' in mode
    if '+' in mode:
        reading = True
        writing = True

    io_object = RawWrapper(bin_file, mode=mode, name=name)
    if buffering >= 0:
        if reading and writing:
            io_object = io.BufferedRandom(
                io_object,
                buffering or io.DEFAULT_BUFFER_SIZE
            )
        elif reading:
            io_object = io.BufferedReader(
                io_object,
                buffering or io.DEFAULT_BUFFER_SIZE
            )
        elif writing or appending:
            io_object = io.BufferedWriter(
                io_object,
                buffering or io.DEFAULT_BUFFER_SIZE
            )

    if not binary:
        io_object = io.TextIOWrapper(
            io_object,
            encoding=encoding,
            errors=errors,
            newline=newline,
            line_buffering=line_buffering,
        )

    return io_object


def line_iterator(readable_file, size=None):
    """A not terribly efficient char by char line iterator."""
    read = readable_file.read
    line = []
    byte = b'1'
    if size is None or size < 0:
        while byte:
            byte = read(1)
            line.append(byte)
            if byte in b'\n':
                yield b''.join(line)
                del line[:]

    else:
        while byte and size:
            byte = read(1)
            size -= len(byte)
            line.append(byte)
            if byte in b'\n' or not size:
                yield b''.join(line)
                del line[:]
