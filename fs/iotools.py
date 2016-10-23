from __future__ import unicode_literals, print_function
from __future__ import print_function

import io
from io import SEEK_SET, SEEK_CUR


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
        if hasattr(self._f, 'readable'):
            return self._f.readable()
        return 'r' in self.mode

    def writable(self):
        if hasattr(self._f, 'writeable'):
            return self._fs.writeable()
        return 'w' in self.mode

    def seekable(self):
        if hasattr(self._f, 'seekable'):
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
        if self.is_io:
            return self._f.write(data)
        self._f.write(data)
        return len(data)

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
                f,
                mode='r',
                buffering=-1,
                encoding=None,
                errors=None,
                newline=None,
                line_buffering=False,
                **kwargs):
    """Take a Python 2.x binary file and return an IO Stream."""
    r = 'r' in mode
    w = 'w' in mode
    a = 'a' in mode
    binary = 'b' in mode
    if '+' in mode:
        r = True
        w = True

    io_object = RawWrapper(f, mode=mode, name=name)
    if buffering >= 0:
        if r and w:
            io_object = io.BufferedRandom(
                io_object,
                buffering or io.DEFAULT_BUFFER_SIZE
            )
        elif r:
            io_object = io.BufferedReader(
                io_object,
                buffering or io.DEFAULT_BUFFER_SIZE
            )
        elif w or a:
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


def decode_binary(data, encoding=None, errors=None, newline=None):
    """Decode bytes as though read from a text file."""
    return io.TextIOWrapper(
        io.BytesIO(data),
        encoding=encoding,
        errors=errors,
        newline=newline
    ).read()


def line_iterator(f, size=None):
    """A not terribly efficient char by char line iterator."""
    read = f.read
    line = []
    append = line.append
    c = True
    join = b''.join
    is_terminator = b'\n'.__contains__  # True for '\n' and also for ''
    if size is None or size < 0:
        while c:
            c = read(1)
            append(c)
            if is_terminator(c):
                yield join(line)
                del line[:]
    else:
        while c:
            c = read(1)
            append(c)
            if is_terminator(c) or len(line) >= size:
                yield join(line)
                del line[:]


if __name__ == "__main__":  # pragma: nocover
    print("Reading a binary file")
    bin_file = open('tests/data/UTF-8-demo.txt', 'rb')
    with make_stream('UTF-8-demo.txt', bin_file, 'rb') as f:
        print(repr(f))
        print(type(f.read(200)))

    print("Reading a text file")
    bin_file = open('tests/data/UTF-8-demo.txt', 'rb')
    with make_stream('UTF-8-demo.txt', bin_file, 'rt') as f:
        print(repr(f))
        print(type(f.read(200)))

    print("Reading a buffered binary file")
    bin_file = open('tests/data/UTF-8-demo.txt', 'rb')
    with make_stream('UTF-8-demo.txt', bin_file, 'rb', buffering=0) as f:
        print(repr(f))
        print(type(f.read(200)))
