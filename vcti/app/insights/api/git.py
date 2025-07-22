#!/usr/bin/env python

# Copyright (C) 2018 Visual Collaboration Technologies Inc.
# All Rights Reserved.
#
# This file is a property of Visual Collaboration Technologies Inc.
# Unauthorized access, reproduction or redistribution of any kind is prohibited.

from fastapi import APIRouter, Depends, HTTPException
import logging

from vcti.wtf.template.repository import TemplatesRepository
from vcti.wtf.variable.list import Variables
from ..dependencies import templates_repository

logger = logging.getLogger('uvicorn.error')

router = APIRouter()
prefix = "git"
tags = ["git"]


@router.get("/{name}",
            response_model=Variables,
            summary="Get template variables",
            response_description="Templates Variables List")
async def variables(
    name: str,
    templates_repo: TemplatesRepository = Depends(templates_repository)
) -> Variables:
    try:
        template = templates_repo.get_template(name)
        return template.get_variables()
    except:
        raise HTTPException(status_code=404, detail="Template not found")

