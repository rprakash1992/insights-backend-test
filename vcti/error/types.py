#!/usr/bin/env python

# Copyright (C) 2018 Visual Collaboration Technologies Inc.
# All Rights Reserved.
#
# This file is a property of Visual Collaboration Technologies Inc.
# Unauthorized access, reproduction or redistribution of any kind is prohibited.
"""Defines standard exception types using an enumeration."""

from enum import IntEnum
from enum import auto as auto_value


class ExceptionType(IntEnum):
    """
    Enumeration of exception types.

    Attributes:
        UNSPECIFIED: Represents an unspecified error.
        FILE_NOT_FOUND: File not found error.
        FILE_DOES_NOT_EXIST: File does not exist error.
        LICENSE_ERROR: License-related error.
        KEY_ERROR: Key-related error.
        VARIABLE_UNDEFINED: Undefined variable error.
    """

    UNSPECIFIED = 1
    FILE_NOT_FOUND = auto_value()
    FILE_DOES_NOT_EXIST = auto_value()
    LICENSE_ERROR = auto_value()
    KEY_ERROR = auto_value()
    VARIABLE_UNDEFINED = auto_value()
