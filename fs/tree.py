# coding: utf-8
"""Render a FS object as text tree views.

Color is supported on UNIX terminals.
"""

from __future__ import print_function
from __future__ import unicode_literals

import sys

from fs.path import abspath, join, normpath


def render(fs,
           path='/',
           file=None,
           encoding=None,
           max_levels=5,
           with_color=None,
           dirs_first=True,
           exclude=None,
           filter=None):
    """Render a directory structure in to a pretty tree.

    Arguments:
        fs (~fs.base.FS): A filesystem instance.
        path (str): The path of the directory to start rendering
            from (defaults to root folder, i.e. ``'/'``).
        file (io.IOBase): An open file-like object to render the
            tree, or `None` for stdout.
        encoding (str or None): Unicode encoding, or `None` to
            auto-detect.
        max_levels (int or None): Maximum number of levels to
            display, or `None` for no maximum.
        with_color (bool or None): Enable terminal color output,
            or `None` to auto-detect terminal.
        dirs_first (bool): Show directories first.
        exclude (list or None): Option list of directory patterns
            to exclude from the tree render.
        filter (list or None): Optional list of files patterns to
            match in the tree render.

    Returns:
        (int, int): A tuple of ``(<directory count>, <file count>)``.

    """
    file = file or sys.stdout
    if encoding is None:
        encoding = getattr(file, 'encoding', 'utf-8') or 'utf-8'
    is_tty = hasattr(file, 'isatty') and file.isatty()

    if with_color is None:
        is_windows = sys.platform.startswith('win')
        with_color = False if is_windows else is_tty

    if encoding.lower() == 'utf-8' and with_color:
        char_vertline = '│'
        char_newnode = '├'
        char_line = '──'
        char_corner = '└'
    else:
        char_vertline = '|'
        char_newnode = '|'
        char_line = '--'
        char_corner = '`'

    indent = ' ' * 4
    line_indent = char_vertline + ' ' * 3

    def write(line):
        """Write a line to the output.
        """
        print(line, file=file)

    def format_prefix(prefix):
        """Format the prefix lines.
        """
        if not with_color:
            return prefix
        return '\x1b[32m%s\x1b[0m' % prefix

    def format_dirname(dirname):
        """Format a directory name.
        """
        if not with_color:
            return dirname
        return '\x1b[1;34m%s\x1b[0m' % dirname

    def format_error(msg):
        """Format an error.
        """
        if not with_color:
            return msg
        return '\x1b[31m%s\x1b[0m' % msg

    def format_filename(fname):
        """Format a filename.
        """
        if not with_color:
            return fname
        if fname.startswith('.'):
            fname = '\x1b[33m%s\x1b[0m' % fname
        return fname

    def sort_key_dirs_first(info):
        """Get the info sort function with directories first.
        """
        return (not info.is_dir, info.name.lower())

    def sort_key(info):
        """Get the default info sort function using resource name.
        """
        return info.name.lower()

    counts = {"dirs": 0, "files": 0}

    def format_directory(path, levels):
        """Recursive directory function.
        """
        try:
            directory = sorted(
                fs.filterdir(path, exclude_dirs=exclude, files=filter),
                key=sort_key_dirs_first if dirs_first else sort_key
            )
        except Exception as error:
            prefix = ''.join(
                indent if last else line_indent
                for last in levels
            ) + char_corner + char_line
            write("{} {}".format(
                format_prefix(prefix),
                format_error("error ({})".format(error))
            ))
            return
        _last = len(directory) - 1
        for i, info in enumerate(directory):
            is_last_entry = i == _last
            counts['dirs' if info.is_dir else 'files'] += 1
            prefix = ''.join(
                indent if last else line_indent
                for last in levels
            )
            prefix += char_corner if is_last_entry else char_newnode
            if info.is_dir:
                write("{} {}".format(
                    format_prefix(prefix + char_line),
                    format_dirname(info.name)
                ))
                if max_levels is None or len(levels) < max_levels:
                    format_directory(
                        join(path, info.name),
                        levels + [is_last_entry]
                    )
            else:
                write("{} {}".format(
                    format_prefix(prefix + char_line),
                    format_filename(info.name)
                ))

    format_directory(abspath(normpath(path)), [])
    return counts['dirs'], counts['files']
