#!/usr/bin/env python

# Copyright (C) 2018 Visual Collaboration Technologies Inc.
# All Rights Reserved.
#
# This file is a property of Visual Collaboration Technologies Inc.
# Unauthorized access, reproduction or redistribution of any kind is prohibited.
"""Run management API for handling job runs within templates."""

from enum import Enum
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel
from starlette.status import (
    HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
)

from vcti.util.path_utils import FileNameValidator
from vcti.wtf.template.repository import TemplatesRepository

from ..app_context import templates_repository
from .utils import (
    dispatch_with_validation,
    get_existing_template_or_404,
    handle_template_errors,
)

router = APIRouter()
prefix = "runs"
tags = ["runs"]


# --------------------------
# Models and Enums
# --------------------------


class RunListResponse(BaseModel):
    runs: list[str]
    active: str


class RetrievalMode(str, Enum):
    """
    Supported response formats for template retrieval.

    Values:
        STATUS: Returns the run status
    """

    STATUS = "status"


class RunUpdateAction(str, Enum):
    ACTIVATE = "activate"
    CLEAR = "clear"
    EXECUTE = "execute"


retrieval_handlers = {
    RetrievalMode.STATUS: lambda t, r: t.runs.get_run_status(r),
}

run_update_handlers = {
    RunUpdateAction.ACTIVATE: lambda t, r: t.runs.set_active_run(r),
    RunUpdateAction.CLEAR: lambda t, r: t.runs.clear_run(r),
    RunUpdateAction.EXECUTE: lambda t, r: t.runs.execute_run(r),
}


# --------------------------
# Routes
# --------------------------


@router.get(
    "/{template_id}",
    summary="List all runs and the active run",
    response_model=RunListResponse,
)
@handle_template_errors("runs listing")
async def list_runs(
    template_id: str,
    templates_repo: TemplatesRepository = Depends(templates_repository),
) -> RunListResponse:
    """
    List all runs for a given template and return the active run.

    Args:
        template_id (str): Template identifier.
        templates_repo (TemplatesRepository): Dependency-injected repo.

    Returns:
        RunListResponse: Contains runs IDs and the currently active run.
    """
    template = get_existing_template_or_404(template_id, templates_repo)
    return RunListResponse(
        runs=template.runs.get_all_runs(),
        active=template.runs.get_active_run(),
    )


@router.get(
    "/{template_id}/{run_id}",
    summary="Retrieve status of a specific run",
)
@handle_template_errors("run info")
async def get_run_details(
    template_id: str,
    run_id: str,
    mode: RetrievalMode = Query(..., description="Content type to retrieve: 'status'"),
    templates_repo: TemplatesRepository = Depends(templates_repository),
) -> Any:
    """
    Get the status of a specific run.

    Args:
        template_id (str): Template identifier.
        run_id (str): Run identifier.
        mode (str): Data to retrieve (currently only 'status' supported).
        templates_repo (TemplatesRepository): Dependency-injected repo.

    Returns:
        run_status: Run status if mode is 'status', otherwise raises HTTP 400.
    """
    template = get_existing_template_or_404(template_id, templates_repo)
    FileNameValidator.validate(run_id)
    handler = dispatch_with_validation(mode, retrieval_handlers, "retrieval mode")
    return handler(template, run_id).state if mode == RetrievalMode.STATUS else None


@router.put(
    "/{template_id}/{run_id}",
    summary="Create a new run for the template",
)
@handle_template_errors("run creation")
async def create_run(
    template_id: str,
    run_id: str,
    templates_repo: TemplatesRepository = Depends(templates_repository),
) -> str:
    """
    Create a new run folder under the template's runs directory.

    Args:
        template_id (str): Template identifier.
        run_id (str): Desired run identifier to create.
        templates_repo (TemplatesRepository): Dependency-injected repo.

    Returns:
        str: Created run ID.
    """
    template = get_existing_template_or_404(template_id, templates_repo)
    FileNameValidator.validate(run_id)
    if template.runs.has_run(run_id):
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST, detail=f"Run {run_id} already exists"
        )

    return template.runs.create_run(run_id)


@router.patch(
    "/{template_id}/{run_id}",
    summary="Update a specific run",
)
@handle_template_errors("run update")
async def update_run(
    template_id: str,
    run_id: str,
    action: RunUpdateAction = Query(
        ..., description="Action to perform (activate, execute, or clear)"
    ),
    templates_repo: TemplatesRepository = Depends(templates_repository),
):
    """
    Activate, execute or clear a run.
    - Activate makes the run as the active run for the template.
    - Execution creates a new process.
    - Clearing removes the contents of the previous run and allows a new execution.

    Args:
        template_id (str): Template identifier.
        run_id (str): Run to operate on.
        action (RunUpdateAction): Action to perform.
        templates_repo (TemplatesRepository): Dependency-injected repo.

    """
    template = get_existing_template_or_404(template_id, templates_repo)
    FileNameValidator.validate(run_id)
    if not template.runs.has_run(run_id):
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND, detail=f"Run {run_id} not found."
        )

    handler = dispatch_with_validation(action, run_update_handlers, "update action")
    handler(template, run_id)
    return Response(status_code=HTTP_204_NO_CONTENT)
