#!/usr/bin/env python
# Copyright (C) 2018 Visual Collaboration Technologies Inc.
# All Rights Reserved.
#
# This file is the property of Visual Collaboration Technologies Inc.
# Unauthorized access, reproduction, or redistribution of any kind is prohibited.

import logging
from enum import StrEnum
from typing import Any, List, Optional

from fastapi import APIRouter, Body, Depends, File, HTTPException, Query, UploadFile
from pydantic import BaseModel, Field, RootModel
from starlette.status import HTTP_400_BAD_REQUEST

from vcti.wtf.template.metadata import Metadata
from vcti.wtf.template.repository import TemplatesRepository

from ..app_context import templates_repository
from .utils import (
    RenameRequest,
    dispatch_with_validation,
    get_existing_template_or_404,
    handle_template_errors,
    handle_template_list_errors,
)

logger = logging.getLogger("uvicorn.info")

router = APIRouter()
prefix = "templates"
tags = ["templates"]


# --------------------------
# Models
# --------------------------


class TemplateManifest(BaseModel):
    """
    Represents the manifest metadata of a template.

    Attributes:
        id (str): Template identifier.
        metadata (Metadata): Template metadata including title, description, etc.
    """

    id: str = Field(
        ...,
        description="Template ID",
    )
    metadata: Metadata = Field(
        ..., description="Template metadata including title, description, etc."
    )


class TemplateCatalog(RootModel):
    """
    Container for a collection of template manifests.

    Attributes:
        root (List[TemplateManifest]): List of template manifests.
    """

    root: List[TemplateManifest]


class RetrievalMode(StrEnum):
    """
    Supported response formats for template retrieval.

    Values:
        MANIFEST: Returns template metadata in JSON format.
        DOWNLOAD: Returns the complete template package as a downloadable file.
    """

    MANIFEST = "manifest"
    DOWNLOAD = "download"


class ModificationAction(StrEnum):
    """
    Supported actions that modify existing templates.

    Values:
        RENAME: Changes the name/identifier of an existing template.
    """

    RENAME = "rename"


class CreationMethod(StrEnum):
    """
    Supported actions that create new templates from existing ones.

    Values:
        DUPLICATE: Creates a copy of an existing template with a new identifier.
    """

    DUPLICATE = "duplicate"


class Result(BaseModel):
    """
    Standardized API response model for template operations.

    Attributes:
        template (str): Identifier of the affected template.
        message (str): Human-readable description of the operation outcome.
    """

    template: str
    message: str


# --------------------------
# Handler dictionaries for endpoint dispatch
# --------------------------

modification_handlers = {ModificationAction.RENAME: lambda t, r: t.rename(r.new_name)}

creation_handlers = {CreationMethod.DUPLICATE: lambda t: t.duplicate()}

retrieval_handlers = {
    RetrievalMode.MANIFEST: lambda t: TemplateManifest(
        id=t.id, metadata=t.workflow_nodes.metadata()
    ),
    RetrievalMode.DOWNLOAD: lambda t: t.download(),
}


# --------------------------
# Routes
# --------------------------


@router.get(
    "/",
    response_model=TemplateCatalog,
    summary="List all available templates",
    response_description="List of all uploaded templates with their metadata",
)
@handle_template_list_errors("retrieving template list")
async def get_template_list(
    templates_repo: TemplatesRepository = Depends(templates_repository),
) -> TemplateCatalog:
    """
    Retrieve a catalog of all available VCollab Insights script templates.

    This endpoint is typically used to populate template selection interfaces.

    Args:
        templates_repo (TemplatesRepository): Templates repository instance.

    Returns:
        TemplateCatalog: A collection of template manifests containing full metadata.

    Raises:
        HTTPException: 500 error if template listing fails due to server issues.
    """
    templates_list = templates_repo.list_templates()
    return TemplateCatalog(
        root=[
            TemplateManifest(
                id=template.id, metadata=template.workflow_nodes.metadata()
            )
            for template in templates_list
        ]
    )


@router.post(
    "/",
    summary="Upload a new template",
    response_description="Uploaded template name and status",
)
@handle_template_list_errors("upload")
async def post_upload_template(
    file: UploadFile = File(...),
    templates_repo: TemplatesRepository = Depends(templates_repository),
) -> Result:
    """
    Upload a new VCollab Insights script template into the repository.

    The uploaded file should be a valid VCollab Insights Script file.

    Args:
        file (UploadFile): Uploaded template bundle file.
        templates_repo (TemplatesRepository): Templates repository instance.

    Returns:
        Result: Operation status with new template ID.

    Raises:
        HTTPException: 500 error if upload processing fails.
    """
    template = templates_repo.create_template(file)
    return Result(
        template=template.id,
        message=f"File {file.filename or ''} uploaded as template {template.id}.",
    )


@router.get(
    "/{template_id}",
    summary="Get template manifest or bundle",
    response_description="Manifest (JSON) or bundle (binary)",
)
@handle_template_errors("retrieval")
async def get_template(
    template_id: str,
    mode: RetrievalMode = Query(
        ..., description="Content type to retrieve: 'manifest' or 'download'"
    ),
    templates_repo: TemplatesRepository = Depends(templates_repository),
) -> Any:
    """
    Fetch a template's metadata or download the template.

    Supported retrieval modes are:
        - 'manifest': Returns JSON metadata about the template.
        - 'download': Downloads the template data.

    Args:
        template_id (str): Template identifier.
        mode (RetrievalMode): Retrieval mode.
        templates_repo (TemplatesRepository): Templates repository instance.

    Returns:
        TemplateManifest or StreamingResponse: JSON metadata or template download.

    Raises:
        HTTPException: 404 if template not found, 400 for invalid requests.
    """
    template = get_existing_template_or_404(template_id, templates_repo)
    handler = dispatch_with_validation(mode, retrieval_handlers, "retrieval mode")
    return handler(template)


@router.patch(
    "/{template_id}",
    summary="Modify a template (e.g. rename)",
    response_description="Result of the modification",
)
@handle_template_errors("modification")
async def patch_template(
    template_id: str,
    action: ModificationAction = Query(
        ..., description="Modification action to perform (currently only 'rename')"
    ),
    request: Optional[RenameRequest] = Body(
        None, description="Required parameters for the modification action"
    ),
    templates_repo: TemplatesRepository = Depends(templates_repository),
) -> Result:
    """
    Perform modification operations on existing templates.

    Currently supported actions:
        - rename: Changes the identifier/name of the template.

    Requires a request body specifying the new name when renaming.

    Args:
        template_id (str): Template to modify.
        action (ModificationAction): Type of modification to perform.
        request (Optional[RenameRequest]): Parameters required for the action.
        templates_repo (TemplatesRepository): Templates repository instance.

    Returns:
        Result: Operation status with updated template ID.

    Raises:
        HTTPException: 400 for invalid requests, 404 if template not found, 500 for server errors.
    """
    template = get_existing_template_or_404(template_id, templates_repo)

    if action == ModificationAction.RENAME:
        if not request or not request.new_name:
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST, detail="Missing 'new_name' for rename"
            )

    handler = dispatch_with_validation(
        action, modification_handlers, "modification action"
    )
    handler(template, request)

    return Result(
        template=template.id,
        message=f"Template {template_id} is renamed to {template.id}",
    )


@router.post(
    "/{template_id}",
    summary="Perform operations to create new templates from existing ones",
    response_description="Result of the action",
)
@handle_template_errors("template creation")
async def post_derive_template(
    template_id: str,
    method: CreationMethod = Query(
        ..., description="Creation method (Only 'duplicate' is supported for now)"
    ),
    templates_repo: TemplatesRepository = Depends(templates_repository),
) -> Result:
    """
    Create new templates from existing/custom actions (e.g. duplicate).

    Currently supported method:
        - duplicate: Creates a copy of the template with a new identifier.

    Args:
        template_id (str): Template to operate on.
        method (CreationMethod): Type of method to use.
        templates_repo (TemplatesRepository): Templates repository instance.

    Returns:
        Result: Operation status with new template ID.

    Raises:
        HTTPException: 400 for invalid requests, 404 if template not found, 500 for server errors.
    """
    template = get_existing_template_or_404(template_id, templates_repo)

    handler = dispatch_with_validation(method, creation_handlers, "creation method")
    new_template = handler(template)

    return Result(
        template=new_template.id,
        message=f"Template {template_id} duplicated as {new_template.id}",
    )


@router.delete(
    "/{template_id}",
    summary="Delete a template",
    response_description="Deleted template status",
)
@handle_template_errors("deletion")
async def delete_template(
    template_id: str,
    templates_repo: TemplatesRepository = Depends(templates_repository),
) -> Result:
    """
    Delete a template from the repository.

    This operation cannot be undone. All data associated with the template will be permanently deleted.

    Args:
        template_id (str): Template to delete.
        templates_repo (TemplatesRepository): Templates repository instance.

    Returns:
        Result: Confirmation of deletion.

    Raises:
        HTTPException: 404 if template not found, 500 for server errors.
    """
    template = get_existing_template_or_404(template_id, templates_repo)
    template.delete()

    return Result(template=template_id, message=f"Template {template_id} is deleted")
