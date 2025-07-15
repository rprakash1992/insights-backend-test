#!/usr/bin/env python

# Copyright (C) 2018 Visual Collaboration Technologies Inc.
# All Rights Reserved.
#
# This file is a property of Visual Collaboration Technologies Inc.
# Unauthorized access, reproduction or redistribution of any kind is prohibited.
"""
Logging Module

This module provides logging functionality for the VCTI application. It includes utilities for
configuring logging, defining log levels, and setting up loggers.

The module provides:
- `DEFAULT_LOG_MESSAGE_FORMAT`: The default format for log messages.
- `create_logging_config`: A function to create a logging configuration.
- `LogLevelsInfo`: A class or utility for managing log level metadata.
- `logger`: The primary logger instance for the application.
- `setup_logging`: A function to initialize and configure logging for the application.
"""
from .config import DEFAULT_LOG_MESSAGE_FORMAT, create_logging_config
from .levels import LogLevel, LogLevelCoder
from .setup import logger, setup_logging
