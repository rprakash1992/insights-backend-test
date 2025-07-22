#!/usr/bin/env python

# Copyright (C) 2018 Visual Collaboration Technologies Inc.
# All Rights Reserved.
#
# This file is a property of Visual Collaboration Technologies Inc.
# Unauthorized access, reproduction or redistribution of any kind is prohibited.

import logging

from fastapi import APIRouter, Depends, HTTPException
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR

from vcti.wtf.template.repository import TemplatesRepository
from vcti.wtf.variable.list import Variables

from ..app_context import templates_repository
from .utils import get_existing_template_or_404

logger = logging.getLogger("uvicorn.error")

router = APIRouter()
prefix = "var"
tags = ["var"]


@router.get(
    "/{template_id}",
    response_model=Variables,
    summary="Get template variables",
    response_description="Templates Variables List",
)
async def variables(
    template_id: str,
    templates_repo: TemplatesRepository = Depends(templates_repository),
) -> Variables:
    try:
        template = get_existing_template_or_404(template_id, templates_repo)
        return template.workflow_nodes.variables()
    except Exception as e:
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Variables extraction for {template_id} failed: {str(e)}",
        )
