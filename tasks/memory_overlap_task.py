from itertools import product

import numpy as np
from object_recursion.tasks import SizeTask

from object_recursion.object_recursion import ObjectRecursion
from object_recursion.task_base import WrapUpTask


def _flatten_trees(obj_id, trees, visited=None):
    """
    :param [dict] trees:
    :param int obj_id:
    :param set | None visited:
    :return:
    """
    if visited is None:
        visited = set()

    # Get children
    children = set()
    for tree in trees:
        if obj_id in tree:
            children.update(tree[obj_id])

    # Update visited with children
    visited.update(children)

    # Go through children
    descendants = visited
    for child in children:
        descendants.update(_flatten_trees(child, trees, visited=visited))

    # Return
    return descendants


class SizeComparisonTask(WrapUpTask):
    def __init__(self, terminate_at=None, word_size=8):
        super().__init__([SizeTask(terminate_at=terminate_at, word_size=word_size)])

    def wrap_up(self, recurser, *args):
        """
        :param ObjectRecursion recurser:
        :param args:
        :return:
        """
        # Get size task
        size_task = self.tasks[0]  # type: SizeTask

        # Wrap up size tasks
        size_task.wrap_up(recurser, *args)

        # Number and ids of objects
        n_objects = len(args)
        obj_ids = args

        # Matrix with size comparison
        m_sizes = np.ones((n_objects, n_objects)) * np.nan

        # Get reference trees
        trees = [recurser.container_children, recurser.reference_children]

        # Flatten trees under each object
        descendants = dict()
        for obj_id in obj_ids:
            descendants[obj_id] = _flatten_trees(obj_id, trees, visited=None)

        # Actual sizes
        actual_sizes = [size_task.get_conclusion(obj_id, recurser=recurser) for obj_id in obj_ids]

        # Compute overlap in sizes
        for obj1_nr, obj2_nr in product(range(n_objects), range(n_objects)):
            obj1_id = obj_ids[obj1_nr]
            obj2_id = obj_ids[obj2_nr]

            # The actual size can not be computed in the same way, because pointers are not considered shared
            if obj1_id == obj2_id:
                m_sizes[obj1_nr, obj2_nr] = actual_sizes[obj1_nr]
                continue

            # Shared descendants
            shared = descendants[obj1_id].intersection(descendants[obj2_id])  # type: set

            # Remove objects contained in other objects (to avoid counting objects twice)
            pruning = True
            objects_to_check = list(shared)
            while pruning:
                pruning = False

                # Get all children of each object and remove from shared
                while objects_to_check:
                    obj_id = objects_to_check.pop()

                    # Get children
                    children = set()
                    if obj_id in recurser.container_children:
                        children.update(set(recurser.container_children[obj_id]))
                    if obj_id in recurser.reference_children:
                        children.update(set(recurser.reference_children[obj_id]))

                    # Avoid removing self
                    children.difference_update([obj_id])

                    # Get only children in shared
                    shared.difference_update(children)

            # Shared size
            shared_size = 0
            for obj_id in shared:
                shared_size += size_task.get_conclusion(obj_id, recurser=recurser)

            # Store in matrix
            m_sizes[obj1_nr, obj2_nr] = shared_size

        return m_sizes


if __name__ == "__main__":
    import pandas as pd

    # Recurser
    comparison_task = SizeComparisonTask()
    recurser = ObjectRecursion(tasks=[comparison_task])

    # Shared objects
    a = ((7, 8), 9)
    b = ["hey", {chr(ord("a") + idx): chr(ord("a") + idx) for idx in range(28)}]

    obj1 = [1, [2, 3, a]]
    obj2 = [4, a, 5, b]
    obj3 = (10, 11, (b, 12))

    # Determine size overlap of objects
    results = recurser.recurse(obj1, obj2, obj3)[0]

    # Determine sizes of shared objects
    ab_sizes = recurser.recurse(a, b)[0].diagonal()

    # Dataframe
    frame = pd.DataFrame(results, index=["obj1", "obj2", "obj3"], columns=["obj1", "obj2", "obj3"])

    print("Object and shared memory consumption:")
    print(frame)

    print("")
    formatter = "Object '{name}' is shared by {objs}, and consumes {size} Bytes"
    print(formatter.format(name="a",
                           objs="obj1 and obj2",
                           size=int(ab_sizes[0])))
    print(formatter.format(name="b",
                           objs="obj2 and obj3",
                           size=int(ab_sizes[1])))
