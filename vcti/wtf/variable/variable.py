#!/usr/bin/env python

# Copyright (C) 2018 Visual Collaboration Technologies Inc.
# All Rights Reserved.
#
# This file is a property of Visual Collaboration Technologies Inc.
# Unauthorized access, reproduction or redistribution of any kind is prohibited.
"""Defines the Pydantic model for workflow parameters."""

from typing import Any, Optional

from pydantic import BaseModel, Field

from vcti.util.enum_coder import EnumCoder

from .type import VariableType

VARIABLE_TYPE_CODER = EnumCoder(
    VariableType,
    value_generator=lambda enum_var: enum_var.value,
    default=VariableType.AUTO_DETECT,
)


class Variable(BaseModel):
    """A user variable with a name, type, and default value."""

    name: str = Field(..., description="The name of the variable.")
    description: Optional[str] = Field(
        default=None, description="A brief description of the variable."
    )
    type: VARIABLE_TYPE_CODER.Literal = Field(
        default=VARIABLE_TYPE_CODER.default,
        description=f'The type of the variable. Supported values: {"/".join(VARIABLE_TYPE_CODER.list)}. Default: {VARIABLE_TYPE_CODER.default}.',
    )
    value: Optional[Any] = Field(
        default=None,
        description="The current value of the variable. If not provided, the default value will be used.",
    )
    default: Any = Field(..., description="The default value of the variable.")

    def get_value(self) -> Any:
        """Returns the current value of the variable if set, otherwise returns the default value."""
        return self.value if self.value is not None else self.default

    def __str__(self) -> str:
        """Returns the name of the variable as a string."""
        return self.name
