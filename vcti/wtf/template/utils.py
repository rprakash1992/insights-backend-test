#!/usr/bin/env python

# Copyright (C) 2018 Visual Collaboration Technologies Inc.
# All Rights Reserved.
#
# This file is a property of Visual Collaboration Technologies Inc.
# Unauthorized access, reproduction or redistribution of any kind is prohibited.
"""
Utility methods
"""

import time
import uuid

def create_unique_str() -> str:
    """
    Generate a fixed-length unique identifier combining a timestamp and random string.
    
    Returns:
        str: A 19-character string in the format: <10-digit timestamp>_<8-char random>
        Example: "1689345678_ab3d7f2e"
    
    Note:
        - Timestamp ensures temporal ordering
        - UUID provides collision resistance
        - Fixed length of 19 characters (10 + 1 + 8)
    """
    timestamp = str(int(time.time()))  # 10-digit timestamp
    random_str = uuid.uuid4().hex[:8]  # 8-character random string
    return f"{timestamp}_{random_str}"