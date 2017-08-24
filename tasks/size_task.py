import sys
from collections import namedtuple
from typing import Tuple, Iterable, Dict
import numpy as np

from object_recursion.object_recursion import ObjectRecursion
from object_recursion.task_base import TreeRecursionTask


def _dprint_indent(string, verbose):
    if verbose:
        print("  " * verbose + string)


class SizeTask(TreeRecursionTask):

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
        self.pointer_size = word_size

        # Ensure items are not counted twice
        self._already_counted = None  # type: set
        self._current_path = None  # type: list

        # Termination markers
        _terminate_at = ObjectRecursion.BaseTerminators
        if terminate_at is not None:
            if isinstance(terminate_at, (list, tuple)):
                _terminate_at += list(terminate_at)
            else:
                _terminate_at.append(terminate_at)
        self._terminate_at = tuple(set(_terminate_at))

    def enter_object(self, *, obj, edge, parent, recurser):
        pass

    def intermediate_initialize(self):
        # Ensure items are not counted twice
        self._already_counted = set()
        self._current_path = []

    def initialize(self):
        self._object_conclusion = dict()
        self._current_path = []
        self._already_counted = set()

    def _note_object_finished(self, *, obj_id, obj, edge, parent, recurser):
        # Note that this size has been returned
        self._already_counted.add(obj_id)

    def get_conclusion(self, obj_id, recurser=None, include_pointer=False):
        # If object has already been observed
        if obj_id in self._already_counted:
            size = 0

        # If this objects conclusion has already been computed
        elif obj_id in self._object_conclusion:
            size = self._object_conclusion[obj_id]

        # Otherwise estimate size
        else:
            size = sys.getsizeof(recurser.objects[obj_id])

        # Add pointer
        if include_pointer:
            size += self.pointer_size

        return size

    def get_size(self, obj_id):
        return self._object_conclusion[obj_id]

    def _finish_key_val_pair(self, obj_id, recurser):
        """
        :param int obj_id: ID of object
        :param ObjectRecursion recurser: Recursive search system.
        """
        # Get info
        obj = recurser.objects[obj_id]

        # Key and value keys
        key_id, value_id = recurser.container_children[obj_id]

        # Get objects
        key = recurser.objects[key_id]
        value = recurser.objects[value_id]

        # Sizes (check if used before)
        key_size = value_size = 0
        if key_id not in self._already_counted:
            key_size = self._finish_object(obj_id=key_id, edge=Dict, parent=obj_id, recurser=recurser)
        if value_id not in self._already_counted:
            value_size = self._finish_object(obj_id=value_id, edge=Dict, parent=obj_id, recurser=recurser)

        # Note object-representation
        self._object_conclusion[obj_id] = (key_size, value_size)
        return key_size, value_size

    def terminate(self, obj):
        return isinstance(obj, self._terminate_at)

    def _termination_conclusion(self, *, obj_id, obj, edge, parent, recurser):
        if self.terminate(obj):
            return True, self.get_conclusion(obj_id=obj_id, recurser=recurser)  # sys.getsizeof(obj)
        else:
            return False, None

    def _stop_recursion_conclusion(self, *, obj_id, obj, edge, parent, recurser):
        include_pointer = self._include_poiner(parent=parent, edge=edge)

        # Return conclusion
        return self.get_conclusion(obj_id=obj_id, recurser=recurser, include_pointer=include_pointer)

    def _include_poiner(self, *, parent, edge):
        # Include pointer if object is found by reference
        include_pointer = True
        if parent is None:
            # Top objects pointer is not relevant
            include_pointer = False
        if edge == Iterable:
            # Iterables pointers are already included
            include_pointer = False

        # Pointers deactivated, because is seems like sys.getsizeof() always includes pointers.
        return False

    def _ensure_processed(self, obj_id, obj, recurser, edge, parent):
        if (isinstance(obj, Dict) or isinstance(obj, Iterable)) and obj_id not in recurser.container_children:
            recurser._recurse(obj, obj_id, edge=edge, parent=parent)

    def _non_termination_conclusion(self, *, obj_id, obj, edge, parent, recurser):
        include_pointer = self._include_poiner(parent=parent, edge=edge)

        # Return conclusion
        size = self.get_conclusion(obj_id=obj_id, recurser=recurser, include_pointer=include_pointer)

        # TODO: This is not an elegant solution, but it seems to fix a bug
        self._ensure_processed(obj_id=obj_id, obj=obj, recurser=recurser, edge=edge, parent=parent)

        # Dictionaries - add size of keys and values
        if isinstance(obj, Dict):
            try:
                if len(recurser.container_children[obj_id]) > 0:
                    inside_objects = recurser.container_children[obj_id]

                    # Split keys and values
                    inside_objects = list(zip(*[self._finish_key_val_pair(obj_id=val, recurser=recurser)
                                                for val in inside_objects]))
                    key_sizes, value_sizes = inside_objects

                    # Add
                    size += int(sum(key_sizes) + sum(value_sizes))
            except KeyError as e:
                raise e

        # If object is iterable - go through contained objects
        elif isinstance(obj, Iterable):
            if len(recurser.container_children[obj_id]) > 0:
                inside_objects = recurser.container_children[obj_id]

                # Finish insides and compute size
                size += int(sum([self._finish_object(obj_id=child, edge=Iterable, parent=obj_id, recurser=recurser)
                                 for child in inside_objects]))

        # Custom objects
        # Attribute dictionary
        if obj_id in recurser.reference_children:
            if len(recurser.reference_children[obj_id]) > 0:
                referenced_objects = recurser.reference_children[obj_id]
                the_edge = ObjectRecursion.ClassDict

                size += int(sum([self._finish_object(obj_id=child, edge=the_edge, parent=obj_id, recurser=recurser)
                                 for child in referenced_objects]))

        return size


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

    bob = namedtuple("Bob", "a, b, c")
    array = np.array([1, 2, 3])
    array2 = np.array([[1, "b"], [3, 4]])

    formatter = "{!s: <50}: {!s: <17}: {!s: <17}: {!s: <17}"

    looper1 = Looper()
    looper2 = Looper()
    looper3 = Looper()
    looper1.a = looper2
    looper2.a = looper3
    looper3.a = looper1

    cont_looper1 = [1, 2, looper2] + [1] * 100
    cont_looper2 = [2, cont_looper1]
    cont_looper3 = [4, cont_looper2]
    cont_looper1[1] = cont_looper3

    items = [
        1,
        2.3,
        None,
        False,
        "hello",
        [],
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
        looper1,
        cont_looper1,
        [1] * 100,
        {val: 1 for val in range(100)}
    ]

    def truncate(string, length=45):
        return string[:length] + (string[length:] and ' ..')

    print(formatter.format("Object", "asizeof()", "recurser-system", "sys.getsizeof()"))
    print("-" * 105)
    for obj in items:
        print(
            formatter.format(truncate(whitespace.sub(" ", repr(obj))),
                             asizeof(obj),
                             recurser.recurse(obj)[0][0],
                             sys.getsizeof(obj))
        )

