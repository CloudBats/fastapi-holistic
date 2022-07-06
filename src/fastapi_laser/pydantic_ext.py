from typing import Callable

import pydantic.typing


def validator(
    *fields: str,
    pre: bool = False,
    each_item: bool = False,
    always: bool = False,
    check_fields: bool = True,
    whole: bool = None,
    allow_reuse: bool = True,
) -> Callable[[pydantic.typing.AnyCallable], classmethod]:
    """A modified version of the original with allow_reuse defaulting to True.

    Intended for use when subclassing settings classes,
    as all validators will be reused."""
    return pydantic.validator(
        *fields,
        pre=pre,
        each_item=each_item,
        always=always,
        check_fields=check_fields,
        whole=whole,
        allow_reuse=allow_reuse,
    )


def update_empty_attrs_from_secrets(obj: pydantic.BaseSettings, secrets: dict[str, str], *attrs: str) -> None:
    """
    Populates the given attributes with secrets from a dictionary
    based on keys composed from the class and attribute names.
    Non-empty attributes are skipped.

    Secret key format example:
    MyClass().my_attribute -> myclass_my_attribute
    """
    if not secrets:
        return

    for attr in attrs:
        if not getattr(obj, attr):
            setattr(obj, attr, secrets[f"{obj.__class__.__name__.lower()}_{attr}"])


def update_empty_attrs_from_other(obj: pydantic.BaseSettings, other: pydantic.BaseSettings, *attrs: str) -> None:
    """
    Populates the given attributes with non-empty attributes from another object
    based on corresponding keys. The other object must contain the target attributes.
    Non-empty attributes in the original object are skipped.
    """
    if not other:
        return

    for attr in attrs:
        if not getattr(obj, attr) and getattr(other, attr):
            setattr(obj, attr, getattr(other, attr))
