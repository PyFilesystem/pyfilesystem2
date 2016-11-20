from __future__ import unicode_literals

def make_repr(class_name, *args, **kwargs):
    """Generate a repr string."""
    arguments = [repr(arg) for arg in args]
    arguments.extend([
        "{}={!r}".format(name, value)
        for name, (value, default) in kwargs.items()
        if value != default
    ])
    return "{}({})".format(class_name, ', '.join(arguments))