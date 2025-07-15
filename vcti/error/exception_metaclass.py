#!/usr/bin/env python

# Copyright (C) 2018 Visual Collaboration Technologies Inc.
# All Rights Reserved
#
# This file is a property of Visual Collaboration Technologies Inc.
# Unauthorized access, reproduction or redistribution of any kind is prohibited.
"""Defines a metaclass for dynamically creating custom exceptions with default messages."""

from typing import Any, Type, TypeVar, Tuple, Dict

T = TypeVar("T", bound="ExceptionMeta")


class ExceptionMeta(type):
    """
    Metaclass for defining custom exceptions with a default message.

    - If an exception is instantiated without arguments,
      it uses the `default_message` from the class.
    - If an argument is provided, it behaves like a standard exception.

    Example:
        class CustomError(metaclass=ExceptionMeta,
                          default_message="A custom error occurred"):
            pass

        raise CustomError()  # Uses default message
        raise CustomError("Custom message")  # Uses provided message
    """

    default_message: str

    def __call__(cls: Type[T], *args: Any, **kwargs: Any) -> T:
        """Creates an instance of the exception class, using default message if none is provided."""
        obj = cls.__new__(cls, *args, **kwargs)
        default_message = getattr(cls, "default_message", None)
        obj.__init__(*args if args else (default_message,), **kwargs)
        return obj

    def __new__(
        mcs: Type[T],
        name: str,
        bases: Tuple[type, ...],
        attrs: Dict[str, Any],
        *args: Any,
        **kwargs: Any
    ) -> T:
        """Dynamically creates a new exception class that inherits from `Exception`."""
        attrs["default_message"] = kwargs.get("default_message", "An error occurred")
        return super().__new__(mcs, name, (Exception,), attrs)
