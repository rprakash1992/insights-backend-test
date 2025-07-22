#!/usr/bin/env python

# Copyright (C) 2018 Visual Collaboration Technologies Inc.
# All Rights Reserved.
#
# This file is a property of Visual Collaboration Technologies Inc.
# Unauthorized access, reproduction or redistribution of any kind is prohibited.
"""
Utility methods
"""

from pathlib import Path

from vcti.util.short_uid import ShortUID


def make_duplicate_name(path: Path) -> str:
    """Generate a unique name for a duplicate file or directory."""
    return f"{path.stem}_copy_{ShortUID.quick()}{path.suffix}"
