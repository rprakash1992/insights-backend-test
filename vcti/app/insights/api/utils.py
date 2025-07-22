#!/usr/bin/env python

# Copyright (C) 2018 Visual Collaboration Technologies Inc.
# All Rights Reserved.
#
# This file is the property of Visual Collaboration Technologies Inc.
# Unauthorized access, reproduction, or redistribution of any kind is prohibited.

import logging
import time
import uuid
from functools import partial, wraps
from typing import Any, Awaitable, Callable, Dict, List, Optional

from fastapi import HTTPException
from fastapi import Path as FPath
from pydantic import BaseModel, Field, field_validator
from starlette.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
    HTTP_500_INTERNAL_SERVER_ERROR,
)

from vcti.wtf.template.repository import TemplatesRepository

logger = logging.getLogger("uvicorn.info")


def get_existing_template_or_404(template_id: str, repo: TemplatesRepository):
    """Fetches a template from the repository or raises an HTTP 404 if not found.

    Args:
        template_id: Template identifier
        repo: Templates repository instance

    Returns:
        The requested template object if found

    Raises:
        HTTPException: 404 error if template doesn't exist
    """
    template = repo.get_template(template_id)
    if not template:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"Template with ID {template_id} not found",
        )
    return template


def validate_file_path(
    file_path: str = FPath(
        ...,
        description="Path within the template (e.g., 'folder/file.txt'). Use forward slashes only.",
    )
) -> List[str]:
    """
    Validates a path string and converts it to a list of path components.
    Rejects Windows-style backslashes.

    Args:
        file_path (str): Raw path string from the URL.

    Returns:
        List[str]: List of path segments (e.g., ['folder', 'file.txt'])

    Raises:
        HTTPException: If backslashes are used in the path.
    """
    if not file_path:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail="File/directory path is not provided",
        )
    if "\\" in file_path:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail="Path must use forward slashes (/) only. Backslashes (\\) are not allowed.",
        )
    return file_path.strip("/").split("/")


def validate_file_name(new_name: str) -> str:
    if "/" in new_name or "\\" in new_name:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail="New name must not contain path separators.",
        )
    return new_name


def validate_new_name(
    new_name: str = FPath(..., description="New name for the file or folder")
) -> str:
    if "/" in new_name or "\\" in new_name:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail="New name must not contain path separators.",
        )
    return new_name


def validate_target_path(
    target_path: str = FPath(
        ..., description="Path like 'template_name/folder/file.txt'"
    )
) -> str:
    if "\\" in target_path:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail="Path must use forward slashes (/) only. Backslashes (\\) are not allowed.",
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


def dispatch_with_validation(key, handlers: dict, operation_name: str):
    if key not in handlers:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=f"Unsupported {operation_name}: {key}",
        )
    return handlers[key]


# --------------------------
# Error Handling Decorator invoked from API methods
# --------------------------


def handle_errors(
    operation: str,
    *,
    log_format: Optional[str] = None,
    log_args: Optional[Dict[str, str]] = None,
):
    def decorator(func: Callable[..., Awaitable[Any]]):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except HTTPException:
                raise
            except Exception as e:
                if log_format:
                    log_data = {k: kwargs.get(v, "") for k, v in log_args.items()}
                    logger.exception(
                        log_format.format(operation=operation, error=e, **log_data)
                    )

                raise HTTPException(
                    status_code=HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"{operation.capitalize()} failed: {str(e)}",
                )

        return wrapper

    return decorator


# --------------------------
# Reusable error handlers with fixed logging configuration
# --------------------------

handle_template_list_errors = partial(
    handle_errors, log_format='Error during "{operation}" : {error}', log_args={}
)


handle_template_errors = partial(
    handle_errors,
    log_format='Error during "{operation}" on template "{template_id}": {error}',
    log_args={"template_id": "template_id"},
)


handle_template_fs_errors = partial(
    handle_errors,
    log_format='Error during "{operation}" on path "{file_path}" of template "{template_id}": {error}',
    log_args={"template_id": "template_id", "file_path": "file_path"},
)
