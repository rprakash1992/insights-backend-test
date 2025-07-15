#!/usr/bin/env python

# Copyright (C) 2018 Visual Collaboration Technologies Inc.
# All Rights Reserved.
#
# This file is the property of Visual Collaboration Technologies Inc.
# Unauthorized access, reproduction, or redistribution of any kind is prohibited.

from fastapi import (
    APIRouter,
    UploadFile,
    File,
    HTTPException,
    Depends,
    Body,
    Form,
)
from starlette.responses import FileResponse, StreamingResponse
from typing import Union
from pydantic import BaseModel
import logging

from vcti.util.path_tree import PathTree
from vcti.wtf.template.repository import TemplatesRepository

from ..dependencies import templates_repository
from .utils import (
    template_id_and_path,
    validate_new_name,
    validate_target_path,
    create_unique_file_name,
    RenameRequest,
)


logger = logging.getLogger("uvicorn.error")

router = APIRouter()
prefix = "fs"
tags = ["fs"]


class Result(BaseModel):
    """
    Represents the result of a file system operation.
    """
    template: str
    path: str
    message: str


# FastAPI (like Starlette underneath) matches routes in the order they are defined
# The standard and correct approach while defining FastAPI routes is to
#     Always define more specific routes before generic path-capturing ones.
# Endpoints with more components should be defined earlier and the endpoints with
# less components should be defined later.
# Ex: The endpoint definitions should be in the following order:
#     - "/{name}/download"
#     - "/{name}"
#     - "/"
#
# Why?
#   Imagine that we define two method:
#      @router.post("/{target_path:path}")
#      @router.post("/{target_path:path}/duplicate")
#   If you use command like: 
#      /api/v1/fs/hello-world/source/duplicate
#   It invokes the first method as it matches first. The second method never gets
#   invoked.
#   This is why, the order is critical, especially when path items are involved.
#   To avoid issues, we use this order all the time, because we may need to add
#   path items at some stage.
#
# You can change the order of appearance of the endpoints in the documentation using
# the `openapi_tags` parameter.

"""
 PATCH /fs/{target_path}/rename + body
     - Cleaner, extensible, JSON-friendly
     - Slightly more complex clients
   Preferred in REST design when
     - You're modifying resource metadata (like renaming),
     - The new value (new_name) is not naturally part of the resource hierarchy (e.g., not a sub-path),
     - You want cleaner, extensible APIs.

 PATCH /fs/{target_path}/rename/{new_name}
     - Easy to call from browser or CLI (no JSON needed)
     - Not great for complex inputs, URL encoding issues with names
"""

@router.patch(
    "/{target_path:path}/rename2/{new_name}",
    #tags=["item_op"],
    summary="Rename a file or directory",
    response_description="Rename result with status"
)
async def rename2(
    target_path: str = Depends(validate_target_path),
    new_name: str = Depends(validate_new_name),
    templates_repo: TemplatesRepository = Depends(templates_repository)
) -> Result:
    """
    Renames a file or folder in the template structure.

    Args:
        target_path (str): Path to the original file/folder.
        new_name (str): New file name

    Returns:
        Result: Result of the rename operation.
    """
    try:
        template_id, relative_path = template_id_and_path(target_path)
        template = templates_repo.get_template(template_id)
        new_path = template.files.rename(relative_path, new_name)

        return Result(
            template=template.id,
            path=str(new_path),
            message=f'Path "{target_path}" is renamed to "{new_path}"'
        )
    except Exception:
        logger.exception("Rename failed for path: %s", target_path)
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.patch(
    "/{target_path:path}/rename",
    #tags=["item_op"],
    summary="Rename a file or directory",
    response_description="Rename result with status"
)
async def rename(
    target_path: str = Depends(validate_target_path),
    request: RenameRequest = Body(...),
    templates_repo: TemplatesRepository = Depends(templates_repository)
) -> Result:
    """
    Renames a file or folder in the template structure.

    Args:
        target_path (str): Path to the original file/directory.
        request (RenameRequest): Request body.

    Returns:
        Result: Result of the rename operation.
    """
    try:
        template_id, relative_path = template_id_and_path(target_path)
        template = templates_repo.get_template(template_id)
        new_path = template.files.rename(relative_path, request.new_name)

        return Result(
            template=template.id,
            path=str(new_path),
            message=f'Path "{target_path}" is renamed to "{new_path}"'
        )
    except Exception:
        logger.exception("Rename failed for path: %s", target_path)
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.get(
    "/{target_path:path}/tree",
    #tags=["item_op"],
    summary="Get children items as a tree for a directory",
    response_description="Children items as a tree structure"
)
async def get_tree(
    target_path: str = Depends(validate_target_path),
    templates_repo: TemplatesRepository = Depends(templates_repository)
) -> PathTree:
    """
    Returns directory or file structure at the given path.

    Args:
        target_path (str): Template path string.

    Returns:
        PathTree: Directory and file structure.
    """
    try:
        template_id, relative_path = template_id_and_path(target_path)
        template = templates_repo.get_template(template_id)
        return template.files.get_file_tree(relative_path)
    except Exception:
        logger.exception("Failed to get info for path: %s", target_path)
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.get(
    "/{target_path:path}/download",
    #tags=["item_op"],
    summary="Download a file or directory as a stream",
    response_description="Streamed file or zip archive",
    response_model=None
)
async def download(
    target_path: str = Depends(validate_target_path),
    templates_repo: TemplatesRepository = Depends(templates_repository)
) -> Union[FileResponse, StreamingResponse]:
    """
    Downloads a file or folder from the template.

    Args:
        target_path (str): File or folder path.

    Returns:
        StreamingResponse: Streamed content.
    """
    try:
        template_id, relative_path = template_id_and_path(target_path)
        template = templates_repo.get_template(template_id)
        return template.files.download_file_or_directory(relative_path)
    except Exception:
        logger.exception("Download failed for path: %s", target_path)
        raise HTTPException(status_code=404, detail="Path not found")


@router.post(
    "/{target_path:path}/duplicate",
    #tags=["item_op"],
    summary="Duplicate a file or directory",
    response_description="Duplication result with status",
    response_model=Result
)
async def duplicate(
    target_path: str = Depends(validate_target_path),
    templates_repo: TemplatesRepository = Depends(templates_repository)
) -> Result:
    """
    Duplicates a file or directory.

    Args:
        target_path (str): Path to file/folder to duplicate.

    Returns:
        Result: Result of the duplication operation.
    """
    try:
        template_id, relative_path = template_id_and_path(target_path)
        template = templates_repo.get_template(template_id)
        new_file_path = template.files.duplicate(relative_path)
        return Result(
            template=template.id,
            path=str(new_file_path),
            message=f'Path "{target_path}" is duplicated to "{new_file_path}"'
        )
    except Exception:
        logger.exception("Duplication failed for path: %s", target_path)
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.post(
    "/{target_path:path}",
    #tags=["item"],
    summary="Upload a file to the given path",
    response_description="Uploaded file path and operation status",
)
async def upload(
    target_path: str = Depends(validate_target_path),
    file: UploadFile = File(...),
    is_directory: bool = Form(False, description="Is the upload corresponds to a directory?"),
    templates_repo: TemplatesRepository = Depends(templates_repository)
) -> Result:
    """
    Uploads a file to the given path inside a template.

    Args:
        target_path (str): Nested directory path inside the template.
        file (UploadFile): The file to upload.
        is_directory (bool): If True, it is a archive that needs to be extracted as a directory.

    Returns:
        Result: Operation status and file path info.
    """
    try:
        template_id, relative_path = template_id_and_path(target_path)
        template = templates_repo.get_template(template_id)
        if not relative_path:
            raise HTTPException(status_code=400, detail="No directory path provided after template")

        result_path = template.files.upload_file_or_directory(relative_path, file, is_directory)
        return Result(
            template=template.id,
            path=target_path,
            message=f'File data is uploaded to path "{result_path}"'
        )
    except HTTPException:
        raise
    except Exception:
        logger.exception("Upload failed for path: %s", target_path)
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.delete(
    "/{target_path:path}",
    #tags=["item"],
    summary="Delete a file or directory",
    response_description="Deletion result with status"
)
async def delete(
    target_path: str = Depends(validate_target_path),
    templates_repo: TemplatesRepository = Depends(templates_repository)
) -> Result:
    """
    Deletes a file or directory at the given path.

    Args:
        target_path (str): Template path to delete.

    Returns:
        Result: Operation result.
    """
    try:
        template_id, relative_path = template_id_and_path(target_path)
        template = templates_repo.get_template(template_id)
        result_path = template.files.delete(relative_path)
        return Result(
            template=template.id,
            path=target_path,
            message=f'Path "{result_path}" is deleted.'
        )
    except Exception:
        logger.exception("Deletion failed for path: %s", target_path)
        raise HTTPException(status_code=404, detail="Path not found")
