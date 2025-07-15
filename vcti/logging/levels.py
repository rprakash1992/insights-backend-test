#!/usr/bin/env python

# Copyright (C) 2018 Visual Collaboration Technologies Inc.
# All Rights Reserved.
#
# This file is a property of Visual Collaboration Technologies Inc.
# Unauthorized access, reproduction or redistribution of any kind is prohibited.
"""Dynamic LogLevel enum."""

import logging
from enum import IntEnum

from vcti.util.enum_coder import EnumCoder

# Ensure that custom levels are added to standard log levels
from .custom_level import CustomLogLevel

stanard_log_levels = logging._nameToLevel
# standard_log_levels = logging.getLevelNamesMapping()  # for Python 3.11+
custom_log_levels = {l.name: l.value for l in CustomLogLevel}

log_levels = {
    **stanard_log_levels,
    **custom_log_levels,
}

LogLevel = IntEnum("LogLevel", log_levels)

LogLevelCoder = EnumCoder(
    LogLevel,
    value_generator=lambda enum_var: enum_var.name.lower().replace("_", "-"),
    default=LogLevel.INFO,
)
