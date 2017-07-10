from collections import namedtuple
from numbers import Number
from typing import Tuple, Dict, Iterable, Callable

import numpy as np

from object_recursion.object_recursion import ObjectRecursion, RecursionTask


# TODO: Do time-comparison between rtype and ContainerTreePrintTask/ObjectRecurser


class TypeCheckTask(RecursionTask):
    @property
    def interests(self):
        return (Tuple,
                Dict,
                np.ndarray,
                Iterable
                )

    def __init__(self, delimiter="[", or_divider="|", and_divider=",", map_divider=": ",
                 numpy_notation="np dim"):
        super().__init__()
        self.delimiter = delimiter
        self.or_divider = or_divider
        self.and_divider = and_divider
        self.map_divider = map_divider
        self.numpy_notation = numpy_notation

        # Conversions
        self.l, self.r = self._delimiter_types(delimiter=delimiter)

        # Results on objects
        self._object_conclusion = None

    def enter_object(self, *, obj, edge, parent, recurser):
        pass

    def initialize(self):
        self._object_conclusion = dict()

    @staticmethod
    def _delimiter_types(delimiter="["):
        if delimiter in "p()":
            return "(", ")"
        elif delimiter in "s[]":
            return "[", "]"
        elif delimiter in "c{}":
            return "{", "}"
        else:
            return "<", ">"

    def _finish_dict(self, obj_id, obj_name, recurser):
        """
        :param int obj_id:
        :param str obj_name:
        :param ObjectRecursion recurser:
        :return:
        """
        # Collect insides
        inside = ""
        if len(recurser.container_children[obj_id]) > 0:
            inside_objects = recurser.container_children[obj_id]

            # Split keys and values
            inside_objects = list(zip(*[self._finish_key_val_pair(val, recurser=recurser) for val in inside_objects]))
            keys, values = inside_objects
            keys = set(keys)
            values = set(values)

            # Make insides string
            inside = self.l + self.or_divider.join(keys) + self.map_divider + self.or_divider.join(values) + self.r

        # Final string
        return obj_name + inside

    def _finish_key_val_pair(self, obj_id, recurser):
        """
        :param int obj_id:
        :param ObjectRecursion recurser:
        :return:
        """

        # Get info
        obj = recurser.objects[obj_id]

        # Split pair
        key, value = obj

        # Representation
        key_representation = self._finish_object(obj_id=id(key), edge=Dict, parent=obj_id, recurser=recurser)
        value_representation = self._finish_object(obj_id=id(value), edge=Dict, parent=obj_id, recurser=recurser)

        # Note object-representation
        self._object_conclusion[obj_id] = (key_representation, value_representation)
        return key_representation, value_representation

    def _finish_iterable(self, obj_id, obj_name, recurser):
        """
        :param int obj_id:
        :param str obj_name:
        :param ObjectRecursion recurser:
        :return:
        """
        return obj_name + self._finish_iterable_insides(obj_id=obj_id, recurser=recurser)

    def _finish_iterable_insides(self, obj_id, recurser):
        """
        :param int obj_id:
        :param ObjectRecursion recurser:
        :return:
        """
        # Collect insides
        inside = ""
        if len(recurser.container_children[obj_id]) > 0:
            inside_objects = recurser.container_children[obj_id]

            # Finish insides
            inside_objects = set([self._finish_object(obj_id=child, edge=Iterable, parent=obj_id, recurser=recurser)
                                  for child in inside_objects])

            inside = self.l + self.or_divider.join(inside_objects) + self.r

        # Final string
        return inside

    def _finish_numpy(self, obj_id, obj_name, recurser):
        """
        :param int obj_id:
        :param str obj_name:
        :param ObjectRecursion recurser:
        :return:
        """
        insides = self._finish_iterable_insides(obj_id=obj_id, recurser=recurser)

        # Remove underscores in numpy
        if "keep_" not in self.numpy_notation:
            insides = insides.replace("_", "")

        # Insert numpy-marker
        if "np" in self.numpy_notation:
            obj_name = "np." + obj_name

        # Replace name with dimensional notation
        if "dim" in self.numpy_notation:
            obj_name = obj_name.replace("ndarray", "{}darray".format(len(recurser.objects[obj_id].shape)))

        # Final string
        return obj_name + insides

    def _finish_tuple(self, obj_id, obj_name, recurser):
        """
        :param int obj_id:
        :param str obj_name:
        :param ObjectRecursion recurser:
        :return:
        """
        # Collect insides
        inside = ""
        if len(recurser.container_children[obj_id]) > 0:
            inside_objects = recurser.container_children[obj_id]

            # Finish insides
            inside_objects = [self._finish_object(obj_id=child, edge=Tuple, parent=obj_id, recurser=recurser)
                              for child in inside_objects]

            inside = self.l + self.and_divider.join(inside_objects) + self.r

        # Final string
        return obj_name + inside

    def _finish_object(self, *, obj_id, edge, parent, recurser):
        """
        Finish the task on the object, using information about all children.
        :param int obj_id: ID of object
        :param ObjectRecursion recurser: Recursive search system.
        :return:
        """
        # Check if already noted
        if obj_id in self._object_conclusion:
            return self._object_conclusion[obj_id]

        # Get info
        if obj_id not in recurser.objects:
            pass
        obj = recurser.objects[obj_id]
        obj_name = "None" if obj is None else type(obj).__name__

        # Simple types
        if isinstance(obj, (str, bool, Number, int, float, complex)):
            representation = obj_name

        # Containers
        else:
            # Objects with direct representation
            if isinstance(obj, Callable):
                representation = "{}()".format(obj.__name__)

            # Unknown container
            elif obj_id not in recurser.container_children:
                representation = obj_name

            # Containers
            elif isinstance(obj, Tuple):
                representation = self._finish_tuple(obj_id=obj_id, obj_name=obj_name, recurser=recurser)
            elif isinstance(obj, Dict):
                representation = self._finish_dict(obj_id=obj_id, obj_name=obj_name, recurser=recurser)
            elif isinstance(obj, np.ndarray):
                representation = self._finish_numpy(obj_id=obj_id, obj_name=obj_name, recurser=recurser)
            elif isinstance(obj, Iterable):
                representation = self._finish_iterable(obj_id=obj_id, obj_name=obj_name, recurser=recurser)

            # Everything else
            else:
                representation = obj_name

        # Note object-representation
        self._object_conclusion[obj_id] = representation
        return self._object_conclusion[obj_id]


if __name__ == "__main__":
    import re

    # For making prints one-liners
    whitespace = re.compile("[\s\n]+")

    # Recursion object
    type_checker = TypeCheckTask()
    the_recurser = ObjectRecursion(tasks=[type_checker])


    # Example classes and types
    class Foo(object):
        pass


    def bar():
        pass


    bob = namedtuple("Bob", "a, b, c")
    array = np.array([1, 2, 3])
    array2 = np.array([[1, "b"], [3, 4]])

    formatter = "{!s: <50}: {!s}"

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

    print(formatter.format("Object", "recurser-system"))
    print("-" * 75)
    for obj in items:
        print(formatter.format(whitespace.sub(" ", repr(obj)),
                               the_recurser.recurse(obj)[0][0]))
