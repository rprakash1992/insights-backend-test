#!/usr/bin/env python

# Copyright (C) 2018 Visual Collaboration Technologies Inc.
# All Rights Reserved.
#
# This file is a property of Visual Collaboration Technologies Inc.
# Unauthorized access, reproduction or redistribution of any kind is prohibited.
"""Utility functions for retrieving exception details."""

from .exception_mappings import (
    EXCEPTION_CLASS_TO_ERROR_CODE,
    EXCEPTION_NAME_TO_TYPE,
    EXCEPTION_TYPE_TO_CLASS,
)
from .types import ExceptionType


def exception_class(exception_type_name: str) -> type:
    """
    Retrieves the exception class corresponding to a given exception type name.

    Args:
        exception_type_name (str): Name of the exception type (case-insensitive).

    Returns:
        type: Corresponding exception class, or `Exception` if not found.
    """
    exception_type = EXCEPTION_NAME_TO_TYPE.get(exception_type_name.lower())
    return EXCEPTION_TYPE_TO_CLASS.get(exception_type, Exception)


def error_code(exception_cls: type) -> int:
    """
    Retrieves the error code corresponding to a given exception class.

    Args:
        exception_cls (type): The exception class.

    Returns:
        int: Corresponding error code, or `ExceptionType.UNSPECIFIED.value` if not found.
    """
    return EXCEPTION_CLASS_TO_ERROR_CODE.get(
        exception_cls, ExceptionType.UNSPECIFIED.value
    )
