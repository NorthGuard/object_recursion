import random
import numpy as np
from collections import namedtuple
from typing import Iterable, Dict, Callable, Tuple


def _type_recursive_iterable(obj, sampling, or_divider, l, r):
    # Get type-strings of elements in iterable (recursive)
    if sampling is None:
        tps = list(set(rtype(e) for e in obj))
    else:
        tps = list(set(rtype(e) for e in random.sample(list(obj), sampling)))

    # Get name of object
    name = type(obj).__name__

    # String for output
    string = f"{name}{l}" + or_divider.join(tps) + r

    return string


def _type_recursive_dict(obj, sampling, or_divider, map_divider, l, r):
    # Get type-strings of keys and values (recursive)
    if sampling is None:
        tps = set((rtype(k), rtype(v)) for (k, v) in obj.items())
    else:
        tps = set((rtype(k), rtype(v)) for (k, v) in random.sample(obj.items(), sampling))

    # Get key-types and value-types
    key_types = set(k for (k, v) in tps)
    value_types = set(v for (k, v) in tps)

    # String for keys and values
    key_type_string = or_divider.join(key_types)
    value_type_string = or_divider.join(value_types)

    # Make final string
    string = f"dict{l}{key_type_string}{map_divider}{value_type_string}{r}"

    return string


def _type_recursive_tuple(obj, sampling, and_divider, l, r):
    # Get type-strings of elements in tuple (recursive)
    if sampling is None:
        tps = [rtype(e) for e in obj]
    else:
        tps = [rtype(e) for e in random.sample(list(obj), sampling)]

    # Get name of object
    name = type(obj).__name__

    # Make final string
    string = f"{name}{l}" + and_divider.join(tps) + r

    return string


def _type_recursive_numpy(obj, show_numpy_dimensions, sampling, or_divider, l, r):
    # See if obj is numpy-primitive
    if not isinstance(obj, np.ndarray):
        return type(obj).__name__

    # Get name of object
    name = type(obj).__name__

    # Items
    items = obj.ravel()

    # Get type-strings of elements in object (recursive)
    if sampling is None:
        tps = list(set(rtype(e) for e in items))
    else:
        tps = list(set(rtype(e) for e in random.sample(items, sampling)))

    # Get number of dimensions
    dims = len(obj.shape)

    # Insert number of dimensions if needed
    if show_numpy_dimensions:
        if name == "ndarray":
            name = f"np.{dims}darray"
        else:
            name = f"np.{name}({dims})"

    # String for output
    string = f"{name}{l}" + or_divider.join(tps) + r

    return string


def _delimiter_types(delimiter="<"):
    if delimiter in "p()":
        return "(", ")"
    elif delimiter in "s[]":
        return "[", "]"
    elif delimiter in "c{}":
        return "{", "}"
    else:
        return "<", ">"


def rtype(obj, sampling=None, delimiter="[", or_divider="|", and_divider=",", map_divider=": ",
          show_numpy_dimensions=True):

    # Get delimiters
    l, r = _delimiter_types(delimiter=delimiter)

    # Get type of object
    t = type(obj)

    # NoneType -> None
    if obj is None:
        return "None"

    # Basic types (str is also iterable, so it must be handled here - the others could be moved to default)
    if t in {int, str, bool, float, complex}:
        return t.__name__

    # Tuples
    if isinstance(obj, Tuple):
        return _type_recursive_tuple(obj, sampling=sampling, and_divider=and_divider, l=l, r=r)

    # Dictionaries
    if isinstance(obj, Dict):
        return _type_recursive_dict(obj, sampling=sampling, or_divider=or_divider, map_divider=map_divider, l=l, r=r)

    # Numpy special case
    if t.__module__ == "numpy":
        return _type_recursive_numpy(obj, show_numpy_dimensions=show_numpy_dimensions,
                                     sampling=sampling, or_divider=or_divider, l=l, r=r)

    # Iterables
    if isinstance(obj, Iterable):  # This category includes objects with specific formatting like dict, tuple and str
        return _type_recursive_iterable(obj, sampling=sampling, or_divider=or_divider, l=l, r=r)

    # Functions / callable
    if isinstance(obj, Callable):
        return "{}()".format(obj.__name__)

    # Default
    return t.__name__


if __name__ == "__main__":
    import re

    # For making prints one-liners
    whitespace = re.compile("[\s\n]+")

    # Example classes and types
    class Foo(object):
        pass

    def bar():
        pass

    bob = namedtuple("Bob", "a, b, c")
    array = np.array([1, 2, 3])
    array2 = np.array([[1, "b"], [3, 4]])

    items = [
        1,
        2.3,
        None,
        False,

        "hello",
        [1, 2, 3],
        ["a", "b"],
        [1, "h"],
        (False, 1, "2"),
        {1.2, 2.3, 3.4},
        [[1, 2, 3], [4, 5, 6], [7, 8, 9]],
        [(1, 'a'), (2, 'b')],
        {1: 'b', 2: 'c'},
        {1: 'b', 2: None},
        [Foo()],
        [bar],
        bob(1, 2, 3),
        array,
        array2
    ]

    # Run a ton of examples
    for obj in items:
        print("{: <50}".format(whitespace.sub(" ", repr(obj))), ":", rtype(obj))
