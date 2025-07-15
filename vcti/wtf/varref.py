#!/usr/bin/env python

# Copyright (C) 2018 Visual Collaboration Technologies Inc.
# All Rights Reserved.
#
# This file is a property of Visual Collaboration Technologies Inc.
# Unauthorized access, reproduction or redistribution of any kind is prohibited.
"""Defines the VariableReference class"""

from pydantic import BaseModel, Field


class VariableReference(BaseModel):
    """Represents a variable reference in YAML."""

    var_name: str = Field(description="The name of the referenced variable.")
