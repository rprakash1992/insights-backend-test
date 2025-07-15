#!/usr/bin/env python

# Copyright (C) 2018 Visual Collaboration Technologies Inc.
# All Rights Reserved.
#
# This file is a property of Visual Collaboration Technologies Inc.
# Unauthorized access, reproduction or redistribution of any kind is prohibited.
"""Create a Custom Logger Class for Enhanced Logging"""

import logging
from enum import IntEnum
from typing import Type


def create_custom_logger(name: str, custom_levels: Type[IntEnum]) -> logging.Logger:
    """
    Factory to create a logger instance with custom log levels and methods, without affecting global logging state.
    """

    class CustomLogger(logging.Logger):
        """
        Custom logger class that adds custom logging levels and methods.
        """

        pass

    for level in custom_levels:
        method_name = level.name.lower()

        def log_for_level(self, msg, *args, _level=level, **kwargs):
            if self.isEnabledFor(_level.value):
                self._log(_level.value, msg, args, stacklevel=2, **kwargs)

        setattr(CustomLogger, method_name, log_for_level)
        logging.addLevelName(level.value, level.name)

    logger = CustomLogger(name)

    # Add custom level names locally to this logger (just for formatting/logging)
    logger._custom_level_names = {
        lvl.value: lvl.name for lvl in custom_levels
    }  # not used by `logging`, just helpful
    return logger
