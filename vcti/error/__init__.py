#!/usr/bin/env python

# Copyright (C) 2018 Visual Collaboration Technologies Inc.
# All Rights Reserved.
#
# This file is a property of Visual Collaboration Technologies Inc.
# Unauthorized access, reproduction or redistribution of any kind is prohibited.
"""Error handling framework for custom and system exceptions.

This package provides a framework for defining custom exceptions, mapping them to error codes,
and handling system errors with errno integration.
"""

from .factory import *
from .system_error import system_error
from .utils import *
