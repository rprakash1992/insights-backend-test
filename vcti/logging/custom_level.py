#!/usr/bin/env python

# Copyright (C) 2018 Visual Collaboration Technologies Inc.
# All Rights Reserved.
#
# This file is a property of Visual Collaboration Technologies Inc.
# Unauthorized access, reproduction or redistribution of any kind is prohibited.
"""Defines custom logging levels beyond standard log levels."""

from enum import IntEnum


class CustomLogLevel(IntEnum):
    """Additional logging levels for more granular control."""

    TRACE = 5  # Used for capturing the most detailed, low-level flow
    # of the application and positioned below DEBUG.
    VERBOSE = 15  # Messages that are more detailed than INFO but less
    # granular than DEBUG
