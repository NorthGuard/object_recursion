import re
from typing import Tuple, Dict, Iterable

import numpy as np

from object_recursion.object_recursion import ObjectRecursion, RecursionTask


class ContainerTreePrintTask(RecursionTask):
    @property
    def interests(self):
        return (Tuple,
                Dict,
                np.ndarray,
                Iterable
                )

    def __init__(self):
        super().__init__()
        self.whitespace = re.compile("[\s\n]+")
        self._object_conclusion = None
        self.depths = None

    def initialize(self):
        self._object_conclusion = dict()
        self.depths = dict()

    def _finish_container(self, obj_id, depth, recurser):
        """
        Finish the task on the object, using information about all children.
        :param int obj_id: ID of object
        :param int depth: Depth in tree
        :param ObjectRecursion recurser:
        :return:
        """
        # Check if already processed
        if obj_id in self._object_conclusion:
            return self._object_conclusion[obj_id]

        # Print me
        string = "  " * depth + self.whitespace.sub(" ", repr(recurser.objects[obj_id]))

        # Print insides
        if obj_id in recurser.container_children and len(recurser.container_children[obj_id]) > 0:
            inside_objects = recurser.container_children[obj_id]

            for child in inside_objects:
                string += "\n" + self._finish_object(obj_id=child, edge=Iterable, parent=obj_id, recurser=recurser)

        return string

    def _finish_object(self, *, obj_id, edge, parent, recurser):
        """
        Finish the task on the object, using information about all children.
        :param int obj_id: ID of object
        :param ObjectRecursion recurser: Recursive search system.
        :return:
        """
        self.depths[obj_id] = len(recurser.container_root_path)
        result = self._finish_container(obj_id=obj_id, depth=len(recurser.container_root_path), recurser=recurser)
        self._object_conclusion[obj_id] = result
        return result

    def enter_object(self, obj, edge, parent, recurser):
        pass


if __name__ == "__main__":

    obj = [1, [2, 3, ((4, 5), 7)]]

    # Recursion object
    tree_task = ContainerTreePrintTask()
    the_recurser = ObjectRecursion(tasks=[tree_task])

    print(the_recurser.recurse(obj)[0][0])
