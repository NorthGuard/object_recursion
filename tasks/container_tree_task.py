import re
from typing import Tuple, Dict, Iterable

import numpy as np

from object_recursion.object_recursion import ObjectRecursion
from object_recursion.task_base import TreeRecursionTask


class ContainerTreePrintTask(TreeRecursionTask):

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

    def initialize(self):
        self._current_path = []
        self._object_conclusion = dict()

    def _produce_name(self, obj_id, recurser):
        if obj_id in recurser.container_root_path:
            depth = recurser.container_root_path.index(obj_id)
        else:
            depth = len(recurser.container_root_path)
        string = "  " * depth + self.whitespace.sub(" ", repr(recurser.objects[obj_id]))
        return string

    def _termination_conclusion(self, *, obj_id, obj, edge, parent, recurser):
        if isinstance(obj, tuple(ObjectRecursion.BaseTerminators)):
            return True, self._produce_name(obj_id=obj_id, recurser=recurser)
        return False, None

    def _stop_recursion_conclusion(self, *, obj_id, obj, edge, parent, recurser):
        return self._produce_name(obj_id=obj_id, recurser=recurser)

    def _non_termination_conclusion(self, *, obj_id, obj, edge, parent, recurser):

        # String
        string = self._produce_name(obj_id=obj_id, recurser=recurser)

        # Process insides
        if obj_id in recurser.container_children and len(recurser.container_children[obj_id]) > 0:
            inside_objects = recurser.container_children[obj_id]

            for child in inside_objects:
                string += "\n" + self._finish_object(obj_id=child, edge=Iterable, parent=obj_id, recurser=recurser)

        return string

    def enter_object(self, *, obj, edge, parent, recurser):
        pass


if __name__ == "__main__":

    obj = [1, [2, 3, ((4, 5), 7)]]

    container_looper1 = [1, 2]
    container_looper2 = [2, container_looper1]
    container_looper3 = [3, container_looper2]
    container_looper1[1] = container_looper3

    # Recursion object
    tree_task = ContainerTreePrintTask()
    the_recurser = ObjectRecursion(tasks=[tree_task])

    print(the_recurser.recurse(obj)[0][0], "\n")
    print(the_recurser.recurse(container_looper1)[0][0])
