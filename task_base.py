class RecursionTask:
    def __init__(self):
        self._object_conclusion = None

    @property
    def interests(self):
        raise NotImplementedError

    def initialize(self):
        """
        Initializes the task before running any recursions.
        """
        raise NotImplementedError

    def get_conclusion(self, obj_id, recurser=None):
        return self._object_conclusion[obj_id]

    def intermediate_initialize(self):
        """
        Initializes the task between recursing on two objects.
        """
        pass

    def enter_object(self, *, obj, edge, parent, recurser):
        """
        An object is now being visited.
        :param obj:
        :param edge:
        :param parent:
        :param ObjectRecursion recurser:
        """
        raise NotImplementedError

    def result(self, obj_id, recurser):
        """
        Get result of task on object.
        :param int obj_id:
        :param ObjectRecursion recurser:
        """
        return self._finish_object(obj_id=obj_id, edge=None, parent=None, recurser=recurser)

    def finish_object(self, *, obj_id, edge, parent, recurser):
        if edge in self.interests:
            return self._finish_object(obj_id=obj_id, edge=edge, parent=parent, recurser=recurser)

    def _finish_object(self, *, obj_id, edge, parent, recurser):
        """
        Finish the task on the object, using information about all children.
        :param int obj_id: ID of object
        :param ObjectRecursion recurser: Recursive search system.
        """
        raise NotImplementedError

    def wrap_up(self, recurser, *args):
        results = []
        for obj_id in args:
            results.append(self.result(obj_id, recurser=recurser))
        return results


class TreeRecursionTask(RecursionTask):
    """
    This is a RecursionTask which does avoid infinite loops if objects' references creates loops.
    """

    def __init__(self):
        super().__init__()
        # Loop avoidance
        self._current_path = None  # type: list

    def initialize(self):
        raise NotImplementedError

    @property
    def interests(self):
        raise NotImplementedError

    def _stop_recursion_conclusion(self, *, obj_id, obj, edge, parent, recurser):
        raise NotImplementedError

    def _termination_conclusion(self, *, obj_id, obj, edge, parent, recurser):
        raise NotImplementedError

    def _non_termination_conclusion(self, *, obj_id, obj, edge, parent, recurser):
        raise NotImplementedError

    def _note_object_finished(self, *, obj_id, obj, edge, parent, recurser):
        pass

    def _finish_object(self, *, obj_id, edge, parent, recurser):
        """
        Finish the task on the object, using information about all children.
        :param int obj_id: ID of object
        :param ObjectRecursion recurser: Recursive search system.
        :return:
        """
        if self._current_path is None:
            raise ValueError("TreeRecursionTask._current_path is None. Remember to initialise "
                             "TreeRecursionTask._current_path when implementing a "
                             "subclass of TreeRecursionTask")

        # Check if already noted
        if obj_id in self._object_conclusion:
            return self._object_conclusion[obj_id]

        # Get object
        # TODO: Debugging
        try:
            obj = recurser.objects[obj_id]
        except KeyError as e:
            raise e

        # Termination
        terminate_bool, terminate_return = self._termination_conclusion(obj_id=obj_id,
                                                                        obj=obj,
                                                                        edge=edge,
                                                                        parent=parent,
                                                                        recurser=recurser)
        if terminate_bool:
            conclusion = terminate_return

        # Non-termination objects
        else:

            # Loop reference
            if obj_id in self._current_path:
                conclusion = self._stop_recursion_conclusion(obj_id=obj_id,
                                                             obj=obj,
                                                             edge=edge,
                                                             parent=parent,
                                                             recurser=recurser)

            # Non-terminate object
            else:
                # Note on path (reference-loop avoidance)
                self._current_path.append(obj_id)

                conclusion = self._non_termination_conclusion(obj_id=obj_id,
                                                              obj=obj,
                                                              edge=edge,
                                                              parent=parent,
                                                              recurser=recurser)

        # Remove from path (reference-loop avoidance)
        if self._current_path and self._current_path[-1] == obj_id:
            self._current_path.pop()

        # Note finished object
        self._note_object_finished(obj_id=obj_id,
                                   obj=obj,
                                   edge=edge,
                                   parent=parent,
                                   recurser=recurser)

        # Note object-representation
        self._object_conclusion[obj_id] = conclusion
        return self._object_conclusion[obj_id]

    def enter_object(self, *, obj, edge, parent, recurser):
        raise NotImplementedError


class WrapUpTask(RecursionTask):
    @property
    def interests(self):
        interests = set()
        for task in self.tasks:  # type: RecursionTask
            interests.update(set(task.interests))
        return interests

    def __init__(self, tasks):
        super().__init__()
        self.tasks = tasks  # type: [RecursionTask]

    def intermediate_initialize(self):
        for task in self.tasks:  # type: RecursionTask
            task.intermediate_initialize()

    def enter_object(self, *, obj, edge, parent, recurser):
        for task in self.tasks:  # type: RecursionTask
            task.enter_object(obj=obj, edge=edge, parent=parent, recurser=recurser)

    def _finish_object(self, *, obj_id, edge, parent, recurser):
        for task in self.tasks:  # type: RecursionTask
            task._finish_object(obj_id=obj_id, edge=edge, parent=parent, recurser=recurser)

    def initialize(self):
        for task in self.tasks:  # type: RecursionTask
            task.initialize()

    def wrap_up(self, recurser, *args):
        raise NotImplementedError
