#!/usr/bin/env python

# Copyright (C) 2018 Visual Collaboration Technologies Inc.
# All Rights Reserved.
#
# This file is a property of Visual Collaboration Technologies Inc.
# Unauthorized access, reproduction or redistribution of any kind is prohibited.
"""Class that provides colored logging messages
"""

import colorlog

from .custom_level import CustomLogLevel

default_log_colors = {
    **colorlog.default_log_colors,
    CustomLogLevel.TRACE.name: "cyan",
    CustomLogLevel.VERBOSE.name: "bold_cyan",
}


# Create and return color log formatter
def create_formatter(message_format: str) -> colorlog.ColoredFormatter:
    """
    Creates and returns a colorlog formatter with the specified message format.

    Args:
        message_format (str): The log message format.

    Returns:
        colorlog.ColoredFormatter: Configured formatter instance.
    """
    return colorlog.ColoredFormatter(message_format, log_colors=default_log_colors)
