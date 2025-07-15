#!/usr/bin/env python

# Copyright (C) 2018 Visual Collaboration Technologies Inc.
# All Rights Reserved.
#
# This file is a property of Visual Collaboration Technologies Inc.
# Unauthorized access, reproduction or redistribution of any kind is prohibited.
"""Defines the Pydantic model providing profile information."""

from pydantic import BaseModel, Field, RootModel
from typing import List, Optional, Dict, Any


class ProfileInfo(BaseModel):
    """Metadata and configuration for a single profile."""
    name: str = Field(
        ...,
        description="Display name of the profile"
    )
    description: Optional[str] = Field(
        default=None,
        description="Description of the profile"
    )
    avatar: Optional[str] = Field(
        default=None,
        description="Path to avatar image file"
    )
    tags: List[str] = Field(
        default_factory=list,
        description="Tags for categorizing and filtering profiles"
    )
    attributes: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional custom attributes for the profile"
    )


class Profile(BaseModel):
    """Complete profile representation including its ID and info."""
    id: str = Field(..., description="Unique profile identifier (directory name)")
    info: ProfileInfo = Field(..., description="Profile metadata and configuration")


class ProfileList(RootModel):
    """Collection of available profiles."""
    root: List[Profile] = Field(default_factory=list)


DEFAULT_PROFILE_ID = "default"
DEFAULT_PROFILE = Profile(
    id=DEFAULT_PROFILE_ID,
    info=ProfileInfo(
        name="Default Profile",
        description="The default profile",
        tags=["default"],
        attributes={},
    ),
)

