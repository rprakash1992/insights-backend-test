#!/usr/bin/env python

# Copyright (C) 2018 Visual Collaboration Technologies Inc.
# All Rights Reserved.
#
# This file is a property of Visual Collaboration Technologies Inc.
# Unauthorized access, reproduction or redistribution of any kind is prohibited.
"""Configures logging handlers and levels."""

import logging
from pathlib import Path
from typing import List, Union

from .colorlog_formatter import create_formatter as create_colorlog_formatter
from .config import ConsoleLogConfig, FileLogConfig
from .custom_level import CustomLogLevel

# from .custom_logger import CustomLogger
from .levels import LogLevelCoder
from .logger_factory import create_custom_logger

LOGGER_NAME = "vcti"
# logger = CustomLogger(LOGGER_NAME)
logger = create_custom_logger(LOGGER_NAME, CustomLogLevel)


def setup_logging(
    logging_configurations: List[Union[ConsoleLogConfig, FileLogConfig]],
    propagate: bool = False,
):
    """
    Configures logging for console and file output.

    Args:
        logging_configurations (List[Union[ConsoleLogConfig, FileLogConfig]]): List of log configurations.
        propagate (bool): Determines if log messages propagate to the root logger.

    Raises:
        ValueError: If an invalid log level is specified.
    """
    # Clear existing handlers before setting up new ones
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
        handler.close()

    for config in logging_configurations:
        log_level = LogLevelCoder.decode(config.log_level).value
        handler = None
        if isinstance(config, ConsoleLogConfig):
            handler = logging.StreamHandler()
            handler.setFormatter(
                create_colorlog_formatter(message_format=config.message_format)
                if config.enable_color_log
                else logging.Formatter(fmt=config.message_format)
            )
        elif isinstance(config, FileLogConfig):
            handler = logging.FileHandler(Path(config.file_path).resolve(), mode="w")
            handler.setFormatter(logging.Formatter(config.message_format))

        if handler:
            handler.setLevel(log_level)
            logger.addHandler(handler)

    if logger.handlers:
        logger.setLevel(min(h.level for h in logger.handlers))
    logger.propagate = propagate
