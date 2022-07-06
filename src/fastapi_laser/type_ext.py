from functools import cache
import inspect
import types
from typing import Any


def get_public_data_attribute_pairs(obj: Any, predicate=None) -> list[tuple[str, Any]]:  # noqa: C901
    """Return all public, data kind members of an object as (name, value) pairs sorted by name.

    Optionally, only return members that satisfy a given predicate.

    Modified version of getmembers() in inspect.
    """
    # Despite the complexity, readability is better as a single function
    if inspect.isclass(obj):
        mro = (obj,) + inspect.getmro(obj)
    else:
        mro = ()
    results = []
    processed = set()
    names = dir(obj)
    # :dd any DynamicClassAttributes to the list of names if object is a class;
    # this may result in duplicate entries if, for example, a virtual
    # attribute with the same name as a DynamicClassAttribute exists
    try:
        for base in obj.__bases__:
            for k, v in base.__dict__.items():
                if isinstance(v, types.DynamicClassAttribute):
                    names.append(k)
    except AttributeError:
        pass
    for key in names:
        # First try to get the value via getattr.  Some descriptors don't
        # like calling their __get__ (see bug #1785), so fall back to
        # looking in the __dict__.
        try:
            value = getattr(obj, key)
            # handle the duplicate key
            if key in processed:
                raise AttributeError
        except AttributeError:
            for base in mro:
                if key in base.__dict__:
                    value = base.__dict__[key]
                    break
            else:
                # could be a (currently) missing slot member, or a buggy
                # __dir__; discard and move on
                continue

        if (predicate and not predicate(value)) or not is_public_data_attribute(key, value):
            continue

        results.append((key, value))
        processed.add(key)

    return sorted(results, key=lambda pair: pair[0])


def is_public_data_attribute(name: str, value: Any) -> bool:
    return is_public_attribute(name) and is_data_attribute(value)


def is_data_attribute(obj: Any) -> bool:
    """Returns True if the object is a data type, i.e. not callable.

    Largely inspired from classify_class_attrs() in inspect.
    """
    return not (
        callable(obj)
        or inspect.isroutine(obj)
        or isinstance(
            obj, (staticmethod, types.BuiltinMethodType, classmethod, types.ClassMethodDescriptorType, property)
        )
    )


@cache
def is_public_attribute(name: str) -> bool:
    return not name.startswith("_")
