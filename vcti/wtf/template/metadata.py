#!/usr/bin/env python

# Copyright (C) 2018 Visual Collaboration Technologies Inc.
# All Rights Reserved.
#
# This file is a property of Visual Collaboration Technologies Inc.
# Unauthorized access, reproduction or redistribution of any kind is prohibited.

"""Defines the Pydantic model providing template information."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class Metadata(BaseModel):
    """
    Pydantic model representing the manifest for a workflow node or template.
    """

    title: str = Field(..., description="Script title")
    description: Optional[str] = Field(
        default=None, description="Script description MarkDown file path"
    )
    preview: Optional[str] = Field(
        default=None, description="Preview image file path for the script"
    )
    tags: List[str] = Field(
        default_factory=list,
        description="List of tags associated with the template for searching and filtering.",
    )
    attributes: Dict[str, Any] = Field(
        default_factory=dict,
        description="Attributes associated with the template for searching and filtering.",
    )
