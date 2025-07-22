#!/usr/bin/env python
# Copyright (C) 2018 Visual Collaboration Technologies Inc.
# All Rights Reserved.
#
# This file is the property of Visual Collaboration Technologies Inc.
# Unauthorized access, reproduction, or redistribution of any kind is prohibited.

import logging
from enum import StrEnum
from typing import Any, Optional

from fastapi import (
    APIRouter,
    Body,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
)
from pydantic import BaseModel
from starlette.status import HTTP_400_BAD_REQUEST

from vcti.wtf.template.repository import TemplatesRepository

from ..app_context import templates_repository
from .utils import (
    RenameRequest,
    dispatch_with_validation,
    get_existing_template_or_404,
    handle_template_fs_errors,
    validate_file_path,
)

logger = logging.getLogger("uvicorn.info")

router = APIRouter()
prefix = "fs"
tags = ["fs"]


class RetrievalMode(StrEnum):
    FILE_TREE = "file-tree"
    DOWNLOAD = "download"


class ModificationAction(StrEnum):
    RENAME = "rename"


class AdditionAction(StrEnum):
    UPLOAD = "upload"
    DUPLICATE = "duplicate"


class Result(BaseModel):
    template: str
    path: str
    message: str


retrieval_handlers = {
    RetrievalMode.FILE_TREE: lambda t, p: t.files.get_directory_tree(p),
    RetrievalMode.DOWNLOAD: lambda t, p: t.files.download(p),
}

modification_handlers = {
    ModificationAction.RENAME: lambda t, p, r: t.files.rename(p, r.new_name)
}


@router.post("/{template_id}", summary="Upload a file to a new template")
@handle_template_fs_errors("file upload")
async def post_upload_file(
    template_id: str,
    file: UploadFile = File(...),
    file_path: str = Form(...),
    is_directory: bool = Query(False),
    create_parents: bool = Query(True),
    templates_repo: TemplatesRepository = Depends(templates_repository),
) -> Result:
    template = get_existing_template_or_404(template_id, templates_repo)
    validate_file_path(file_path)
    result_path = template.files.upload(
        file_path, file, is_directory, create_parents, replace_existing=False
    )
    return Result(
        template=template.id,
        path=str(result_path),
        message=f'File data is uploaded to path "{result_path}"',
    )


@router.put("/{template_id}/{file_path:path}", summary="Replace a file in a template")
@handle_template_fs_errors("file replace")
async def put_replace_file(
    template_id: str,
    file_path: str,
    file: UploadFile = File(...),
    is_directory: bool = Query(False),
    templates_repo: TemplatesRepository = Depends(templates_repository),
) -> Result:
    template = get_existing_template_or_404(template_id, templates_repo)
    validate_file_path(file_path)
    result_path = template.files.upload(
        file_path, file, is_directory, create_parents=False, replace_existing=True
    )
    return Result(
        template=template.id,
        path=str(result_path),
        message=f'File replaced at path "{result_path}"',
    )


@router.get(
    "/{template_id}/{file_path:path}", summary="Get file tree or download a file"
)
@handle_template_fs_errors("file retrieval")
async def get_template_file_data(
    template_id: str,
    file_path: str,
    mode: RetrievalMode = Query(
        ..., description="Content type to retrieve: 'file_tree' or 'download'"
    ),
    templates_repo: TemplatesRepository = Depends(templates_repository),
) -> Any:
    template = get_existing_template_or_404(template_id, templates_repo)
    validate_file_path(file_path)
    handler = dispatch_with_validation(mode, retrieval_handlers, "retrieval mode")
    return handler(template, file_path)


@router.patch("/{template_id}/{file_path:path}", summary="Modify a file or directory")
@handle_template_fs_errors("modification")
async def modify_file(
    template_id: str,
    file_path: str,
    action: ModificationAction = Query(
        ..., description="Modification action to perform (currently only 'rename')"
    ),
    request: Optional[RenameRequest] = Body(None),
    templates_repo: TemplatesRepository = Depends(templates_repository),
) -> Result:
    template = get_existing_template_or_404(template_id, templates_repo)
    validate_file_path(file_path)
    if action == ModificationAction.RENAME:
        if not request or not request.new_name:
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST, detail="Missing 'new_name' for rename"
            )

    handler = dispatch_with_validation(
        action, modification_handlers, "modification action"
    )
    new_path = handler(template, file_path, request)

    return Result(
        template=template.id,
        path=str(new_path),
        message=f'File "{file_path}" renamed to "{new_path}"',
    )


@router.delete("/{template_id}/{file_path:path}", summary="Delete a file or directory")
@handle_template_fs_errors("deletion")
async def delete(
    template_id: str,
    file_path: str,
    templates_repo: TemplatesRepository = Depends(templates_repository),
) -> Result:
    template = get_existing_template_or_404(template_id, templates_repo)
    validate_file_path(file_path)
    result_path = template.files.delete(file_path)
    return Result(
        template=template.id,
        path=str(result_path),
        message=f'Path "{result_path}" is deleted.',
    )
