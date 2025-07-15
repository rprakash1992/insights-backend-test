#!/usr/bin/env python

# Copyright (C) 2018 Visual Collaboration Technologies Inc.
# All Rights Reserved.
#
# This file is the property of Visual Collaboration Technologies Inc.
# Unauthorized access, reproduction, or redistribution of any kind is prohibited.

from fastapi import HTTPException, Path as FPath
from pydantic import BaseModel, Field,  field_validator
import time
from typing import Tuple, List
import uuid


def template_id_and_path(target_path: str) -> Tuple[str, List[str]]:
    """
    Splits the input path into the template id and a list of path components.

    Args:
        target_path (str): Input path string, e.g., 'template_name/folder/file.txt'.

    Returns:
        Tuple[str, List[str]]: (template_name, [subpath components])

    Raises:
        RuntimeError: If the path is empty or invalid.
    """
    if not target_path.strip():
        raise RuntimeError("Empty path provided")
    path_components = target_path.strip("/").split("/")
    if not path_components:
        raise RuntimeError("Invalid file path")
    return path_components[0], path_components[1:]


def validate_new_name(
        new_name: str = FPath(
            ...,
            description="New name for the file or folder"
        )
) -> str:
    if "/" in new_name or "\\" in new_name:
        raise HTTPException(
            status_code=400,
            detail="New name must not contain path separators."
        )
    return new_name


def validate_target_path(
        target_path: str = FPath(
            ...,
            description="Path like 'template_name/folder/file.txt'"
        )
) -> str:
    if "\\" in target_path:
        raise HTTPException(
            status_code=400,
            detail="Path must use forward slashes (/) only. Backslashes (\\) are not allowed."
        )
    return target_path


def create_unique_file_name() -> str:
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


class RenameRequest(BaseModel):
    new_name: str = Field(..., description="New name")

    @field_validator("new_name")
    @classmethod
    def no_slashes(cls, v: str) -> str:
        if "/" in v or "\\" in v:
            raise ValueError("Name must not contain slashes or backslashes.")
        return v
