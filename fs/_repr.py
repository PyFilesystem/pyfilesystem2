from __future__ import unicode_literals

def make_repr(class_name, args):
    """Generate a repr string."""
    arguments = [
        "{!s}={!r}".format(name, value)
        for name, value, default in args
        if value != default
    ]
    return "{}({})".format(class_name, ', '.join(arguments))