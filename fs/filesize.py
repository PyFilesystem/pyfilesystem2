from __future__ import unicode_literals

__all__ = ['traditional', 'decimal']



def _to_str(size, suffixes, base):
    try:
        size = int(size)
    except:
        raise ValueError("filesize requires a numeric value, not {!r}".format(size))
    suffixes = ('KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB')
    base = 1024
    if size == 1:
        return '1 byte'
    elif size < base:
        return '{:,} bytes'.format(size)

    for i, suffix in enumerate(suffixes, 2):
        unit = base ** i
        if size < unit:
            break
    return "{:,.1f} {}".format((base * size / unit), suffix)


def traditional(size):
    return _to_str(
        size,
        ('KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'),
        1024
    )


def decimal(size):
    return _to_str(
        size,
        ('kbit', 'Mbit', 'Gbit', 'Tbit', 'Pbit', 'Ebit', 'Zbit', 'Ybit'),
        1024
    )
