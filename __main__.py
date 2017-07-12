import re
import sys
from collections import namedtuple

import numpy as np
import pandas as pd

from object_recursion import rcontainer_tree_str, rsize, rtype, rsize_overlap

try:
    from pympler.asizeof import asizeof
except ImportError:
    def asizeof(*args):
        return "-"

# For making prints one-liners
whitespace = re.compile("[\s\n]+")

def line(length):
    print("-" * length)

def header(text, length):
    formatter = "{:^" + str(length) + "s}"
    print(formatter.format(text))
    increment = int(max(((length - len(text)) / 2) - 5, 0))
    print(" " * increment + "-" * (len(text) + 10))

def truncate(string, length=45):
    return string[:length] + (string[length:] and ' ..')

# #############################################################################################

# Recursive container tree-string
obj = [1, [2, 3, ((4, 5), 7)]]
line_length = 75
print("\n\n")
line(line_length)
header("Recursive container-tree print.", line_length)
line(line_length)
print(obj)
print("\n" + " " * 10 + "Becomes\n")
print(rcontainer_tree_str(obj))

# #############################################################################################

# Example classes and types
class Foo(object):
    pass


def bar():
    pass


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

bob = namedtuple("Bob", "a, b, c")
array = np.array([1, 2, 3])
array2 = np.array([[1, "b"], [3, 4]])

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
    array2,
    looper1,
    cont_looper1,
    long_list
]

# Recursive type prints
line_length = 75
formatter = "{!s: <50}: {!s}"
print("\n\n")
line(line_length)
header("Recursive object-type.", line_length)
print(formatter.format("Object", "rtype()"))
line(line_length)
for obj in items:
    print(formatter.format(truncate(whitespace.sub(" ", repr(obj))),
                           rtype(obj)))

# Recursive size prints
line_length = 105
formatter = "{!s: <50}: {!s: <19}: {!s: <12}: {!s: <19}"
print("\n\n")
line(line_length)
header("Recursive size.", line_length)
print(formatter.format("Object", "pympler.asizeof()", "rsize()", "sys.getsizeof()"))
line(line_length)
for obj in items:
    print(formatter.format(truncate(whitespace.sub(" ", repr(obj))),
                           asizeof(obj),
                           rsize(obj),
                           sys.getsizeof(obj)))

# #############################################################################################

line_length = 75
print("\n\n")
line(line_length)
header("Recursive memory-overlap.", line_length)
line(line_length)

# Shared objects
a = ((7, 8), 9)
b = ["hey", {chr(ord("a") + idx): chr(ord("a") + idx) for idx in range(28)}]

obj1 = [1, [2, 3, a]]
obj2 = [4, a, 5, b]
obj3 = (10, 11, (b, 12))

# Names of objects to process
names = ["obj1", "obj2", "obj3", "long_list", "looper1", "cont_looper1"]

# Objects
objects = [eval(val) for val in names]

# Determine size overlap of objects
results = rsize_overlap(*objects)

# Determine sizes of shared objects
ab_sizes = rsize_overlap(a, b).diagonal()



# Dataframe
frame = pd.DataFrame(results,
                     index=names,
                     columns=names)

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
