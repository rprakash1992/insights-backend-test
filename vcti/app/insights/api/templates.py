#!/usr/bin/env python

# Copyright (C) 2018 Visual Collaboration Technologies Inc.
# All Rights Reserved.
#
# This file is the property of Visual Collaboration Technologies Inc.
# Unauthorized access, reproduction, or redistribution of any kind is prohibited.

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, Body
from starlette.responses import StreamingResponse
from pydantic import BaseModel, Field, RootModel
import logging
from typing import List

from vcti.wtf.template.repository import TemplatesRepository
from vcti.wtf.template.info import TemplateInfo
from ..dependencies import templates_repository
from .utils import RenameRequest

logger = logging.getLogger('uvicorn.error')

router = APIRouter()
prefix = "templates"
tags = ["templates"]


class TemplateManifest(BaseModel):
    id: str = Field(
        ...,
        description="Template Id.",
    )
    info: TemplateInfo = Field(
        ...,
        description="Template information including title, description and others."
    )


TemplateCatalog = RootModel[List[TemplateManifest]]


class Result(BaseModel):
    template: str
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
#      @router.post("/{path_items:path}")
#      @router.post("/{path_items:path}/duplicate")
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
 PATCH /fs/{name}/rename/{new_name}
     - Easy to call from browser or CLI (no JSON needed)
     - Not great for complex inputs, URL encoding issues with names

 PATCH /fs/{name}/rename + body
     - Cleaner, extensible, JSON-friendly
     - Slightly more complex clients
   Preferred in REST design when
     - You're modifying resource metadata (like renaming),
     - The new value (new_name) is not naturally part of the resource hierarchy (e.g., not a sub-path),
     - You want cleaner, extensible APIs.
"""

@router.patch(
    "/{name}/rename2/{new_name}",
    #tags=["item_op"],
    summary="Rename a template",
    response_description="Renamed template name and status"
)
async def rename2(
    name: str,
    new_name: str,
    templates_repo: TemplatesRepository = Depends(templates_repository)
) -> Result:
    """
    Renames the specified template to a new name.
    """
    try:
        template = templates_repo.get_template(name)
        template.rename(new_name)
        return Result(
            template=template.id,
            message=f"Template {name} is renamed to {template.id}"
        )
    except Exception as e:
        logger.exception('Failed to rename template "%s" to "%s"', name, new_name)
        raise HTTPException(status_code=500, detail="Template rename failed")

@router.patch(
    "/{name}/rename",
    #tags=["item_op"],
    summary="Rename a template",
    response_description="Renamed template name and status"
)
async def rename(
    name: str,
    request: RenameRequest = Body(...),
    templates_repo: TemplatesRepository = Depends(templates_repository)
) -> Result:
    """
    Renames the specified template to a new name.
    """
    try:
        template = templates_repo.get_template(name)
        template.rename(request.new_name)
        return Result(
            template=template.id,
            message=f"Template {name} is renamed to {template.id}"
        )
    except Exception as e:
        logger.exception(f"Failed to rename template '{name}' to '{request.new_name}'")
        raise HTTPException(status_code=500, detail="Template rename failed")

@router.get(
    "/{name}/download",
    #tags=["item_op"],
    summary="Download a template",
    response_description="Download stream for the specified template"
)
async def download(
    name: str,
    templates_repo: TemplatesRepository = Depends(templates_repository)
) -> StreamingResponse:
    """
    Streams the specified template for download.
    """
    try:
        template = templates_repo.get_template(name)
        return template.download()
    except Exception as e:
        logger.warning('Template "%s" not found for download', name)
        raise HTTPException(status_code=404, detail="Template not found")

@router.post(
    "/{name}/duplicate",
    #tags=["item_op"],
    summary="Duplicate a template",
    response_description="Duplicated template name and status"
)
async def duplicate(
    name: str,
    templates_repo: TemplatesRepository = Depends(templates_repository)
) -> Result:
    """
    Creates a copy of the specified template.
    """
    try:
        template = templates_repo.get_template(name)
        new_template = template.duplicate()
        return Result(
            template=new_template.id,
            message=f"Template {name} is duplicated to {new_template.id}"
        )
    except Exception as e:
        logger.exception('Failed to duplicate template "%s"', name)
        raise HTTPException(status_code=500, detail="Template duplication failed")

@router.get(
    "/{name}",
    #tags=["item"],
    summary="Get template metadata",
    response_description="Metadata for the specified template"
)
async def get_info(
    name: str,
    templates_repo: TemplatesRepository = Depends(templates_repository)
) -> TemplateManifest:
    """
    Retrieves metadata about a specific template by name.
    """
    try:
        template = templates_repo.get_template(name)
        return TemplateManifest(id=template.id, info=template.get_info())
    except Exception as e:
        logger.warning('Template "%s" not found', name)
        raise HTTPException(status_code=404, detail="Template not found")

@router.delete(
    "/{name}",
    #tags=["item"],
    summary="Delete a template",
    response_description="Deleted template status"
)
async def delete(
    name: str,
    templates_repo: TemplatesRepository = Depends(templates_repository)
) -> Result:
    """
    Deletes the specified template from the repository.
    """
    try:
        templates_repo.get_template(name).delete()
        return Result(
            template=name,
            message=f"Template {name} is deleted"
        )
    except Exception as e:
        logger.warning('Template "%s" could not be deleted', name)
        raise HTTPException(status_code=404, detail="Template not found")

@router.get(
    "/",
    #tags=["group"],
    response_model=TemplateCatalog,
    summary="List all available templates",
    response_description="List of all uploaded templates"
)
async def get_list(
    templates_repo: TemplatesRepository = Depends(templates_repository)
) -> TemplateCatalog:
    """
    Returns a list of available VCollab Insights script templates in the repository.
    """
    try:
        templates_list = templates_repo.list_templates()
        return TemplateCatalog(
            root=[
                TemplateManifest(id=template.id, info=template.get_info())
                for template in templates_list
            ]
        )
    except Exception as e:
        logger.exception("Failed to list templates")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.post(
    "/",
    #tags=["group"],
    summary="Upload a template",
    response_description="Uploaded template name and status"
)
async def upload(
    file: UploadFile = File(...),
    templates_repo: TemplatesRepository = Depends(templates_repository)
) -> Result:
    """
    Uploads a new VCollab Insights script template into the repository.
    """
    try:
        template = templates_repo.create_template(file)
        return Result(
            template=template.id,
            message=f'File {file.filename if file.filename else ""} is uploaded as template {template.id}.'
        )
    except Exception as e:
        logger.exception("Template upload failed")
        raise HTTPException(status_code=500, detail="Template upload failed")
