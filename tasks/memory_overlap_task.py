from itertools import product

import numpy as np
from object_recursion.tasks import SizeTask

from object_recursion.object_recursion import ObjectRecursion
from object_recursion.task_base import WrapUpTask


class SizeComparisonTask(WrapUpTask):
    def __init__(self, terminate_at=None, word_size=8):
        super().__init__([SizeTask(terminate_at=terminate_at, word_size=word_size)])

    def _flatten_trees(self, obj_id, trees, visited=None):
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

        # Go through children
        for child in children:
            if child not in visited:
                visited.add(child)
                visited.update(self._flatten_trees(child, trees, visited=visited))

        # Return
        return visited

    def get_size(self, obj_id, size_task):
        size = size_task.get_size(obj_id)

        # Check if size is a size-tuple (fx key-value-pair sizes)
        if isinstance(size, tuple):
            size = sum(size)

        return size

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
            descendants[obj_id] = self._flatten_trees(obj_id, trees, visited=None)

        # Actual sizes
        actual_sizes = []
        for obj_id in obj_ids:
            actual_sizes.append(self.get_size(obj_id=obj_id, size_task=size_task))

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
            while pruning:
                pruning = False

                # Get all children of each object and remove from shared
                for obj_id in shared:

                    # Get children
                    children = set()
                    if obj_id in recurser.container_children:
                        children.update(set(recurser.container_children[obj_id]))
                    if obj_id in recurser.reference_children:
                        children.update(set(recurser.reference_children[obj_id]))

                    # Avoid removing self
                    children.difference_update([obj_id])

                    # Get objects to remove
                    for_removal = shared.intersection(children)

                    # Check if any objects are to be removed
                    if for_removal:
                        # Get only children in shared
                        shared.difference_update(for_removal)

                        # Still pruning
                        pruning = True
                        break

            # Shared size
            shared_size = 0
            for obj_id in shared:
                shared_size += self.get_size(obj_id=obj_id, size_task=size_task)

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

    class Looper:
        def __init__(self):
            self.a = None

    looper1 = Looper()
    looper2 = Looper()
    looper3 = Looper()
    looper1.a = looper2
    looper2.a = looper3
    looper3.a = looper1

    long_list = [1] * 100

    cont_looper1 = [1, 2, looper2] + long_list
    cont_looper2 = [2, cont_looper1]
    cont_looper3 = [4, cont_looper2]
    cont_looper1[1] = cont_looper3

    # #####################################################################

    names = ["obj1", "obj2", "obj3", "long_list", "looper1", "cont_looper1"]

    # Objects
    objects = [eval(val) for val in names]

    # Determine size overlap of objects
    results = recurser.recurse(
        *objects
    )[0]

    # Determine sizes of shared objects
    ab_sizes = recurser.recurse(a, b)[0].diagonal()

    # Dataframe
    frame = pd.DataFrame(results, index=names, columns=names)

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
    print("Object 'cont_looper1' contains 'looper1'")
    print("Object 'cont_looper1' shares integers with other objects")
