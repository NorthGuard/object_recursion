import random
from numbers import Number
from typing import Tuple, Iterable, Dict, Generator
from object_recursion.task_base import RecursionTask

import numpy as np
from dnc.dnc import DNC


# TODO: Perhaps make a verbosity system
# TODO: Make the recursion able to also: determine memory consumption, determine reference overlap (and memory overlap)


class ObjectRecursion:
    # Order of container-types matters!
    ContainerTypes = (Tuple,
                      Dict,
                      np.ndarray,
                      Iterable)
    ClassDict = "__dict__"
    ClassSlots = "__slots__"
    BaseTerminators = [str, bool, Number, bytes, range, bytearray, Generator, np.ndarray, type(None)]

    def __init__(self, tasks, container_sampling=None, terminate_at=None):
        # Check tasks
        if tasks is None:
            raise ValueError("tasks can not be None.")

        # Termination markers
        _terminate_at = ObjectRecursion.BaseTerminators
        if terminate_at is not None:
            if isinstance(terminate_at, (list, tuple)):
                _terminate_at += list(terminate_at)
            else:
                _terminate_at.append(terminate_at)
        self._terminate_at = tuple(set(_terminate_at))

        # Fields
        self.container_children = None  # type: dict
        self.container_root_path = None  # type: list
        self.reference_children = None  # type: dict
        self.reference_root_path = None  # type: list
        self.objects = None  # type: dict
        self.handled = None  # type: set

        # Store
        self._tasks = tasks  # type: [RecursionTask]
        self._sampling = container_sampling

        # Note wanted edges, depending on tasks
        _reference_interests = [a_type for a_type in [ObjectRecursion.ClassDict, ObjectRecursion.ClassSlots]
                                if any(a_type in task.interests for task in tasks)]
        _interests = [a_type for a_type in list(ObjectRecursion.ContainerTypes)
                      if any(a_type in task.interests for task in tasks)] + _reference_interests
        self._reference_interests = set(_reference_interests)
        self._interests = set(_interests)

    def _initialize(self):
        self.container_children = dict()
        self.container_root_path = []
        self.reference_children = dict()
        self.reference_root_path = []
        self.objects = dict()
        self.handled = set()

    def print_container(self):
        # TODO: This is a debug method. Delete.
        string = "Contained"
        for key in self.container_children.keys():
            string += f"\n  {key}, {self.objects[key]}:"

            for val in self.container_children[key]:
                string += f"\n     {val}, {self.objects[val]}"
        return string

    def recurse(self, *args, verbose=False):
        """
        Recurse through objects in args and pass on results.
        """
        # Initialize
        self._initialize()

        # Reset tasks
        for task in self._tasks:
            task.initialize()

        # IDs of objects in args
        obj_ids = []

        if verbose:
            print(f"Recursing over {len(args)} objects with {len(self._tasks)} task(s).")

        # Go through objects
        for obj_nr, obj in enumerate(args):

            if verbose:
                print(f"\tObject {obj_nr + 1} / {len(args)}")

            # Intermediate initializations of tasks
            if obj_nr > 0:
                for task in self._tasks:  # type: RecursionTask
                    task.intermediate_initialize()

            # Ensure id-consistency
            obj_id = id(obj)
            obj_ids.append(obj_id)

            # Run on object
            self._recurse(obj, obj_id=obj_id)

            # Stop tasks
            # for task_nr, task in enumerate(self._tasks):  # type: RecursionTask
            #     results[task_nr].append(task.result(obj, recurser=self))

        # Wrap up all tasks
        results = []
        for task in self._tasks:
            results.append(task.wrap_up(self, *obj_ids))

        # Return results
        return results

    @staticmethod
    def _get_insides(obj):
        if isinstance(obj, Dict):
            insides = list(obj.items())
        elif isinstance(obj, np.ndarray):
            insides = obj.ravel()
        elif isinstance(obj, (Tuple, set)):
            insides = list(obj)
        elif isinstance(obj, Iterable):
            insides = obj
        else:
            insides = []

        return insides

    @staticmethod
    def _ensure_on_stack(path, obj_id):
        if obj_id not in path:
            path.append(obj_id)

    def _ensure_parent_stack_removal(self, obj_id):
        if obj_id in self.container_root_path:
            self.container_root_path.pop()
        if obj_id in self.reference_root_path:
            self.reference_root_path.pop()

    def _recurse_container(self, *, obj, obj_id, a_type):

        if obj_id in self.container_children:
            inside_ids = self.container_children[obj_id]
            insides = [self.objects[val] for val in inside_ids]
        else:
            # Get insides
            insides = self._get_insides(obj)
            inside_ids = [id(val) for val in insides]
            for val_id, val in zip(inside_ids, insides):
                self.objects[val_id] = val

            self.container_children[obj_id] = inside_ids

        # Note container and object being a parent
        self._ensure_on_stack(path=self.container_root_path, obj_id=obj_id)

        # Check sampling
        if self._sampling is None:
            # Go through all children
            for child, child_id in zip(insides, inside_ids):
                # Don't consider handled objects (avoid loops)
                if child_id not in self.handled:
                    self._recurse(obj=child, edge=a_type, parent=obj, obj_id=child_id)
        else:
            # Go through sample of children
            sample_ids = random.sample(range(len(inside_ids)), self._sampling)

            # Go through container samples
            for sample_id in sample_ids:
                child = insides[sample_id]
                child_id = inside_ids[sample_id]

                # Don't consider handled objects (avoid loops)
                if child_id not in self.handled:
                    self._recurse(obj=child, edge=a_type, parent=obj, obj_id=child_id)

    def _recurse_reference(self, *, obj, obj_id):
        references = []
        reference_types = []
        # reference_ids = []

        # Add references in class-dictionary to references
        if ObjectRecursion.ClassDict in self._reference_interests:
            if hasattr(obj, '__dict__'):
                self._ensure_on_stack(path=self.reference_root_path, obj_id=obj_id)
                children = list(vars(obj).values())
                reference_types += [ObjectRecursion.ClassDict] * len(children)
                references.extend(children)

        # Add references in class-slots to references
        if ObjectRecursion.ClassSlots in self._reference_interests:
            if hasattr(obj, '__slots__'):
                self._ensure_on_stack(path=self.reference_root_path, obj_id=obj_id)
                children = [getattr(obj, s) for s in obj.__slots__]  # if hasattr(obj, s)
                reference_types += [ObjectRecursion.ClassSlots] * len(children)
                references.extend(children)

        # Get reference ids
        reference_ids = [id(val) for val in references]
        self.reference_children[obj_id] = reference_ids
        assert len(references) == len(reference_ids) == len(reference_types)

        # Note object existence
        # TODO: Replace with self.objects.update() statement
        for child, child_id in zip(references, reference_ids):

            # Note existence
            if child_id not in self.objects:
                self.objects[child_id] = child

        # Recurse
        for child, child_id, reference_type in zip(references, reference_ids, reference_types):

            # Don't consider handled objects (avoid loops)
            if child_id not in self.handled:
                self._recurse(obj=child, edge=reference_type, parent=obj, obj_id=child_id)

    def terminate(self, obj):
        return isinstance(obj, self._terminate_at)

    def _recurse(self, obj, obj_id, edge=None, parent=None):
        self.handled.add(obj_id)

        if obj_id is None:
            obj_id = id(obj)

        # Note observation of object
        if obj_id not in self.objects:
            self.objects[obj_id] = obj

        # Perform tasks on nodes
        for task in self._tasks:  # type: RecursionTask
            task.enter_object(obj=obj, edge=edge, parent=parent, recurser=self)

        # Check termination
        if not self.terminate(obj):

            # Containers
            for a_type in ObjectRecursion.ContainerTypes:

                # Check if object is type and type is of interest
                if isinstance(obj, a_type) and a_type in self._interests:
                    # Handle container
                    self._recurse_container(obj=obj, obj_id=obj_id, a_type=a_type)

                    # Mutually exclusive - don't check other types
                    break

            # Class __dict__ and __slots__
            if self._reference_interests:
                # warnings.warn("loop-references are not handled yet", UserWarning)

                self._recurse_reference(obj=obj, obj_id=obj_id)

        # No longer a parent
        self._ensure_parent_stack_removal(obj_id)

        # Finish object
        for task in self._tasks:  # type: RecursionTask
            task._finish_object(obj_id=obj_id,
                                edge=edge,
                                parent=parent,
                                recurser=self)
