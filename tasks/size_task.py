import sys
from collections import namedtuple
from numbers import Number
from typing import Tuple, Iterable, Dict, Generator

import numpy as np

from object_recursion.object_recursion import ObjectRecursion, RecursionTask


def _dprint_indent(string, verbose):
    if verbose:
        print("  " * verbose + string)


class SizeTask(RecursionTask):
    # Order of container-types matters!
    @property
    def interests(self):
        return (Tuple,
                 Dict,
                 Iterable,
                 ObjectRecursion.ClassDict,
                 ObjectRecursion.ClassSlots
                 )

    def __init__(self, terminate_at=None, word_size=8):
        """

        :param list terminate_at: List of additional object, whose size should be determined directly by
                                    sys.getsizeof().
        :param int word_size: Size of a pointer. Should be 8 on a 64bit system and 4 on a 32bit system.
        """
        super().__init__()

        self._object_conclusion = None  # type: dict
        self._current_path = None  # type: list
        self.pointer_size = word_size

        # Termination markers
        _terminate_at = [str, bool, Number, bytes, range, bytearray, Generator, np.ndarray]
        if terminate_at is not None:
            if isinstance(terminate_at, (list, tuple)):
                _terminate_at += list(terminate_at)
            else:
                _terminate_at.append(terminate_at)
        self._terminate_at = tuple(set(_terminate_at))

    def enter_object(self, *, obj, edge, parent, recurser):
        pass

    def initialize(self):
        self._object_conclusion = dict()
        self._current_path = []

    def get_conclusion(self, obj_id, recurser=None):
        if obj_id in self._object_conclusion:
            return self._object_conclusion[obj_id]
        return sys.getsizeof(recurser.objects[obj_id])

    def _finish_key_val_pair(self, obj_id, recurser):
        """
        :param int obj_id: ID of object
        :param ObjectRecursion recurser: Recursive search system.
        """
        # Get info
        obj = recurser.objects[obj_id]

        # Split pair
        key, value = obj

        # Sizes
        key_size = self._finish_object(obj_id=id(key), edge=Dict, parent=obj_id, recurser=recurser)
        value_size = self._finish_object(obj_id=id(value), edge=Dict, parent=obj_id, recurser=recurser)

        # Note object-representation
        self._object_conclusion[obj_id] = (key_size, value_size)
        return key_size, value_size

    def _finish_object(self, *, obj_id, edge, parent, recurser):
        """
        Finish the task on the object, using information about all children.
        :param int obj_id: ID of object
        :param ObjectRecursion recurser: Recursive search system.
        """
        # Check if already noted
        if obj_id in self._object_conclusion:
            return self._object_conclusion[obj_id]

        # Get info
        obj = recurser.objects[obj_id]
        obj_size = sys.getsizeof(obj)

        # Size of object
        size = obj_size

        # Check termination
        if isinstance(obj, self._terminate_at):
            return size

        # Note on path (reference-loop avoidance)
        self._current_path.append(obj_id)

        # Dictionaries - add size of keys and values
        if isinstance(obj, Dict):
            if len(recurser.container_children[obj_id]) > 0:
                inside_objects = recurser.container_children[obj_id]

                # Split keys and values
                inside_objects = list(zip(*[self._finish_key_val_pair(obj_id=val, recurser=recurser)
                                            for val in inside_objects]))
                key_sizes, value_sizes = inside_objects

                # Add
                size += sum(key_sizes) + sum(value_sizes)

        # If object is iterable - go through contained objects
        elif isinstance(obj, Iterable):
            if len(recurser.container_children[obj_id]) > 0:
                inside_objects = recurser.container_children[obj_id]

                # Finish insides and compute size
                size += sum([self._finish_object(obj_id=child, edge=Iterable, parent=obj_id, recurser=recurser)
                             for child in inside_objects])

        # Custom objects
        # Attribute dictionary
        if obj_id in recurser.reference_children:
            if len(recurser.reference_children[obj_id]) > 0:
                referenced_objects = recurser.reference_children[obj_id]

                # Count number of looped references (reference-loop avoidance)
                loop_count = len([1 for val in referenced_objects
                                  if val in self._current_path])
                non_loop_referenced_objects = [val for val in referenced_objects
                                               if val not in self._current_path]

                # Finish references and compute size
                size += sum([self._finish_object(obj_id=child, edge=ObjectRecursion.ClassDict, parent=obj_id,
                                                 recurser=recurser)
                             for child in non_loop_referenced_objects]) + self.pointer_size * loop_count

        # Remove from path (reference-loop avoidance)
        self._current_path.pop()

        # Note object-size
        self._object_conclusion[obj_id] = size
        return self._object_conclusion[obj_id]


if __name__ == "__main__":
    import re
    try:
        from pympler.asizeof import asizeof
    except ImportError:
        def asizeof(*args):
            return "-"

    # For making prints one-liners
    whitespace = re.compile("[\s\n]+")

    # Recursion object
    size_checker = SizeTask()
    recurser = ObjectRecursion(tasks=[size_checker])

    # Example classes and types
    class Foo(object):
        pass


    def bar():
        pass


    class Looper:
        def __init__(self):
            self.a = None

    looper = Looper()
    looper.a = looper

    bob = namedtuple("Bob", "a, b, c")
    array = np.array([1, 2, 3])
    array2 = np.array([[1, "b"], [3, 4]])

    formatter = "{!s: <50}: {!s: <17}: {!s: <17}: {!s: <17}"

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
        Foo(),
        [bar],
        bar,
        bob(1, 2, 3),
        array,
        array2,
        looper
    ]

    print(formatter.format("Object", "asizeof()", "recurser-system", "sys.getsizeof()"))
    print("-" * 105)
    for obj in items:
        print(formatter.format(whitespace.sub(" ", repr(obj)),
                               asizeof(obj),
                               recurser.recurse(obj)[0][0],
                               sys.getsizeof(obj)))
