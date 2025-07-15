#!/usr/bin/env python

# Copyright (C) 2018 Visual Collaboration Technologies Inc.
# All Rights Reserved.
#
# This file is a property of Visual Collaboration Technologies Inc.
# Unauthorized access, reproduction or redistribution of any kind is prohibited.
"""Defines logging configuration parameters using dataclasses."""

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Union

from .levels import LogLevelCoder

# DEFAULT_LOG_MESSAGE_FORMAT = "%(filename)20s:: %(message)s"
# DEFAULT_LOG_MESSAGE_FORMAT = "%(log_color)s%(levelname)s:%(name)s:%(message)s",
DEFAULT_LOG_MESSAGE_FORMAT = "%(message)s"
DEFAULT_COLORLOG_MESSAGE_FORMAT = "%(log_color)s%(levelname)s:     %(reset)s%(message)s"
# DEFAULT_COLORLOG_MESSAGE_FORMAT = (
#    "%(log_color)s%(levelname)s: %(pathname)s %(lineno)d   %(reset)s%(message)s"
# )
# DEFAULT_COLORLOG_MESSAGE_FORMAT = "%(log_color)s%(levelname)-8s:   %(reset)s%(message)s"


@dataclass
class ConsoleLogConfig:
    """
    Configuration for console logging.

    Attributes:
        log_level (str): Logging level (e.g., "INFO", "DEBUG").
        message_format (str): Log message format.
        enable_color_log (bool): Enables colored logging output.
    """

    log_level: LogLevelCoder.Literal = LogLevelCoder.default
    message_format: Optional[str] = None
    enable_color_log: bool = False


@dataclass
class FileLogConfig:
    """
    Configuration for file logging.

    Attributes:
        file_path (Path): Path to log file.
        log_level (str): Logging level.
        message_format (str): Log message format.
    """

    file_path: Path
    log_level: LogLevelCoder.Literal = LogLevelCoder.default
    message_format: Optional[str] = None


def create_logging_config(
    enable_console_log: bool = True,
    enable_color_log: bool = False,
    log_file_path: Optional[Path] = None,
    log_level: LogLevelCoder.Literal = LogLevelCoder.default,
    message_format: Optional[str] = None,
) -> List[Union[ConsoleLogConfig, FileLogConfig]]:
    """
    Generates logging configurations.

    Args:
        enable_console_log (bool): Enables console logging.
        enable_color_log (bool): Enables colored console output.
        log_file_path (Optional[Path]): File path for log storage.
        log_level (str): Logging level.
        message_format (str): Format for log messages.

    Returns:
        List[Union[ConsoleLogConfig, FileLogConfig]]: List of configured logging parameters.
    """
    config_list = []
    if enable_console_log:
        default_message_format = (
            DEFAULT_COLORLOG_MESSAGE_FORMAT
            if enable_color_log
            else DEFAULT_LOG_MESSAGE_FORMAT
        )
        config_list.append(
            ConsoleLogConfig(
                log_level=log_level,
                message_format=(
                    message_format if message_format else default_message_format
                ),
                enable_color_log=enable_color_log,
            )
        )
    if log_file_path:
        config_list.append(
            FileLogConfig(
                file_path=log_file_path,
                log_level=log_level,
                message_format=(
                    message_format if message_format else DEFAULT_LOG_MESSAGE_FORMAT
                ),
            )
        )
    return config_list
