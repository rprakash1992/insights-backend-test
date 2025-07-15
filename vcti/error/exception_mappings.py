#!/usr/bin/env python

# Copyright (C) 2018 Visual Collaboration Technologies Inc.
# All Rights Reserved.
#
# This file is a property of Visual Collaboration Technologies Inc.
# Unauthorized access, reproduction or redistribution of any kind is prohibited.
"""Defines mappings between exception types, classes, and system errors."""

import errno

from .factory import EXCEPTION_TYPE_TO_CLASS
from .types import ExceptionType

# Extend the exception type-to-class mapping with built-in exceptions
EXCEPTION_TYPE_TO_CLASS.update(
    {
        ExceptionType.UNSPECIFIED: Exception,
        ExceptionType.FILE_NOT_FOUND: FileNotFoundError,
        ExceptionType.KEY_ERROR: KeyError,
    }
)

# Map lowercase exception names to their corresponding exception types
EXCEPTION_NAME_TO_TYPE = {et.name.lower(): et for et in EXCEPTION_TYPE_TO_CLASS}

# Map exception classes to their corresponding error codes
EXCEPTION_CLASS_TO_ERROR_CODE = {
    cls: et.value for et, cls in EXCEPTION_TYPE_TO_CLASS.items()
}

# Map system exceptions to their corresponding errno values
EXCEPTION_ERRNO_MAPPING = {
    FileNotFoundError: errno.ENOENT,
    FileExistsError: errno.EEXIST,
    IsADirectoryError: errno.EISDIR,
    NotADirectoryError: errno.ENOTDIR,
}
