from object_recursion.object_recursion import ObjectRecursion
from object_recursion.tasks import TypeCheckTask, SizeTask, ContainerTreePrintTask, \
    SizeComparisonTask


def rtype(obj, container_sampling=None, delimiter="[", or_divider="|", and_divider=",", map_divider=": ",
                 numpy_notation="np dim"):
    """
    Returns a string representation of the type of an object and the objects contained by the object.
    :param obj: Object whose type and internal types are of interest.
    :param int container_sampling: If this is a number, then each container will be sampled with this many samples
        for determining the internal types. That way not every element in large lists, matrices etc. must be
        analysed.
    :param str delimiter: Characters which delimits containers.
        "[": Use square brackets.
        "(": Use parentheses.
        "{": Use curly brackets.
        "<": Use triangle brackets (inequality symbols).
    :param str or_divider: Divider of alternative types (lists)
    :param str and_divider: Divider of sequential types (tuples)
    :param str map_divider: Separates keys from values in dicts etc.
    :param str numpy_notation: Default is "np dim"
        "np" in numpy_notation      :   Append "np." on the numpy types to avoid confusion with same-named types
                                        from other libraries.
        "keep_" in numpy_notation   :   Do not remove the "_"-symbols from numpy-primitives.
        "dim" in numpy_notation     :   Show the number of dimensions of the numpy-arrays.
                                        Fx. show 2darray or 4darray instead of all being ndarray.
    :return: str
    """
    type_checker = TypeCheckTask(delimiter=delimiter, or_divider=or_divider, and_divider=and_divider,
                                 map_divider=map_divider, numpy_notation=numpy_notation)
    the_recurser = ObjectRecursion(tasks=[type_checker], container_sampling=container_sampling)
    return the_recurser.recurse(obj)[0][0]


def rsize(obj, terminate_at=None, word_size=8):
    """
    Returns an integer size of the object in Bytes.
    The size is computed using sys.getsizeof() and recursively looking through all references, without adding size of
    referenced objects twice. It should therefore be a realistic estimate of the memory-consumption of storing directly
    on disk (without compression etc.).
    :param obj: Object whose size is to be determined.
    :param list terminate_at: Objects whose sizes should be directly determined using sys.getsizeof().
        Defaults to: []
        System will always terminate at types: [str, bool, Number, bytes, range, bytearray, Generator, np.ndarray].
    :param int word_size: Size of a pointer on the used machine.
    :return: int
    """
    size_checker = SizeTask(terminate_at=terminate_at, word_size=word_size)
    recurser = ObjectRecursion(tasks=[size_checker])
    return recurser.recurse(obj)[0][0]


def rcontainer_tree_str(obj):
    """
    Returns a string representation of an object and the contained objects.
    Mostly used to should how the recursive system works.
    :param obj: Container to be printed.
    :return: str
    """
    tree_task = ContainerTreePrintTask()
    the_recurser = ObjectRecursion(tasks=[tree_task])
    return the_recurser.recurse(obj)[0][0]


def rsize_overlap(*args, terminate_at=None, word_size=8):
    """
    Computes the sizes of all objects in *args as well as the approximate memory-overlap between the objects.
    :param args: Objects to analyse.
    :param list terminate_at: Objects whose sizes should be directly determined using sys.getsizeof().
        Defaults to: []
        System will always terminate at types: [str, bool, Number, bytes, range, bytearray, Generator, np.ndarray].
    :param int word_size: Size of a pointer on the used machine.
    :return: np.ndarray
    """
    comparison_task = SizeComparisonTask(terminate_at=terminate_at, word_size=word_size)
    recurser = ObjectRecursion(tasks=[comparison_task], terminate_at=terminate_at)
    return recurser.recurse(*args)[0]
