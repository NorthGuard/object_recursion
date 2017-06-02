# type_recursive
Allows for recursively determining types of various Python objects.


### Usage
Calling `type_recursive()` on an object returns a string describing the type and contained types of that object.
```python
from type_recursive import type_recursive

print(type_recursive([1, None, "str"]))
# Prints: list[int|None|str]

print(type_recursive((False, [" "])))
# Prints: tuple[bool,list[str]]
```

The method can also handle user-defined classes.


### Test Script

The main-block of `type_recursive.py`, runs the method on a list of objects and creates the following print.
On the left there is the string-representation of each object as returned by `repr(obj)`, on the right is the 
recursive type returned by `type_recursive(obj)`.

```
1                                                  : int
2.3                                                : float
None                                               : None
False                                              : bool
'hello'                                            : str
[1, 2, 3]                                          : list[int]
['a', 'b']                                         : list[str]
[1, 'h']                                           : list[int|str]
(False, 1, '2')                                    : tuple[bool,int,str]
{1.2, 2.3, 3.4}                                    : set[float]
[[1, 2, 3], [4, 5, 6], [7, 8, 9]]                  : list[list[int]]
[(1, 'a'), (2, 'b')]                               : list[tuple[int,str]]
{1: 'b', 2: 'c'}                                   : dict[int: str]
{1: 'b', 2: None}                                  : dict[int: None|str]
[<__main__.Foo object at 0x0000028E385C0CC0>]      : list[Foo]
[<function bar at 0x0000028E386110D0>]             : list[bar()]
Bob(a=1, b=2, c=3)                                 : Bob[int,int,int]
array([1, 2, 3])                                   : np.1darray[int32]
array([['1', 'b'], ['3', '4']], dtype='<U11')      : np.2darray[str_]
```


### Options

##### Symbols

The symbols below are used in the representation, but can all be changed with optional arguments to 
`type_recursive()`.  

`[]` Delimiters of types contained within another object (fx. lists, tuples or dictionaries).  
`|` Indicates that a mutable object can have various interchangeable types (fx. lists).  
`,` Indicates that an immutable object can have various ordered types (fx. tuples).   
`:` Symbol for the mapping from one type to another (fx. dictionaries).  
`()` Indicates that the passed argument is callable.  

If a user-defined class is both en iterable and callable etc. then it will only be shown as one of those things.

##### Numpy dimensions

Default setting is to show how many dimensions a numpy array has. For example a one-dimensional array will have type 
`np.1darray` while a two-dimentional matrix will have type `np.2darray`. This numbering can be turned off by 
passing `show_numpy_dimensions=False` to `type_recursive()`, in which the two types would both be `np.ndarray`.

##### Sampling

`type_recursive()` by default recursively goes through all objects within an object. 
With large data-structures this can get time-consuming. Therefore one can pass `sampling=X` to `type_recursive()`,
where `X` is an integer. With this argument, `type_recursive()` takes random `X` samples from any 
list/tuple/iterable etc. and creates a type-string based on those sample. 
This is of cause much faster, but one can not be sure that every nested type is reported (for example if
a single `None`-value is hidden between thousands of integers).