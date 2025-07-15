#!/usr/bin/env python

# Copyright (C) 2018 Visual Collaboration Technologies Inc.
# All Rights Reserved.
#
# This file is a property of Visual Collaboration Technologies Inc.
# Unauthorized access, reproduction or redistribution of any kind is prohibited.
"""Defines the Pydantic model for workflow parameters."""

from typing import Any, Dict, List

from pydantic import RootModel

from .variable import Variable


class Variables(RootModel[List[Variable]]):
    def update(self, new_values: Dict[str, Any]) -> None:
        """Update variable values based on a dictionary of new values."""
        for item in self.root:
            if item.name in new_values:
                item.value = new_values[item.name]
