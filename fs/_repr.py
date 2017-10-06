"""Tools to generate __repr__ strings.
"""

from __future__ import unicode_literals

def make_repr(class_name, *args, **kwargs):
    """Generate a repr string.

    Positional arguments should be the positional arguments used to
    construct the class. Keyword arguments should consist of tuples of
    the attribute value and default. If the value is the default, then
    it won't be rendered in the output.

    Example:
        >>> class MyClass(object):
        ...     def __init__(self, name=None):
        ...         self.name = name
        ...     def __repr__(self):
        ...         return make_repr('MyClass', 'foo', name=(self.name, None))
        >>> MyClass('Will')
        MyClass('foo', name='Will')
        >>> MyClass(None)
        MyClass()

    """
    arguments = [repr(arg) for arg in args]
    arguments.extend([
        "{}={!r}".format(name, value)
        for name, (value, default) in sorted(kwargs.items())
        if value != default
    ])
    return "{}({})".format(class_name, ', '.join(arguments))
