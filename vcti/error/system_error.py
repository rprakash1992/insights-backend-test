#!/usr/bin/env python

# Copyright (C) 2018 Visual Collaboration Technologies Inc.
# All Rights Reserved.
#
# This file is a property of Visual Collaboration Technologies Inc.
# Unauthorized access, reproduction or redistribution of any kind is prohibited.
"""Provides an interface for handling system errors with errno integration."""

import errno
import os

from .exception_mappings import EXCEPTION_ERRNO_MAPPING


def system_error(exception_class, *args, **kwargs):
    """
    Creates an instance of the specified exception class with an appropriate errno value.

    Args:
        exception_class (type): The exception class to instantiate.
        *args: Additional positional arguments.
        **kwargs: Additional keyword arguments.

    Returns:
        Exception: An instance of the specified exception class.
    """
    errno_value = EXCEPTION_ERRNO_MAPPING.get(exception_class, errno.EINVAL)
    return exception_class(errno_value, os.strerror(errno_value), *args, **kwargs)
