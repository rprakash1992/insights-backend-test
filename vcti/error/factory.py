#!/usr/bin/env python

# Copyright (C) 2018 Visual Collaboration Technologies Inc.
# All Rights Reserved
#
# This file is a property of Visual Collaboration Technologies Inc.
# Unauthorized access, reproduction or redistribution of any kind is prohibited.
"""Factory module for dynamically creating custom exceptions."""

import inflection

from .exception_metaclass import ExceptionMeta
from .types import ExceptionType


def create_custom_exceptions():
    """
    Dynamically generates custom exception classes for predefined error types.

    Returns:
        dict: A dictionary mapping `ExceptionType` to the corresponding exception class.
    """
    custom_exceptions = {
        ExceptionType.FILE_DOES_NOT_EXIST: "File does not exist",
        ExceptionType.LICENSE_ERROR: "License error",
        ExceptionType.VARIABLE_UNDEFINED: "Variable undefined",
    }

    exception_classes = {}
    for exception_type, default_message in custom_exceptions.items():
        class_name = inflection.camelize(
            exception_type.name.lower()
        )  # Converts FILE_DOES_NOT_EXIST → FileDoesNotExist
        exception_class = ExceptionMeta(
            class_name,
            (),
            {"__doc__": f"Exception raised for {default_message}."},
            default_message=default_message,
        )
        exception_classes[exception_type] = exception_class
        globals()[class_name] = exception_class  # Adds to the global namespace

    return exception_classes


# Generate and store custom exceptions globally
EXCEPTION_TYPE_TO_CLASS = create_custom_exceptions()
