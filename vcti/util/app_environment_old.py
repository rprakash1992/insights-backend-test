#!/usr/bin/env python

# Copyright (C) 2018 Visual Collaboration Technologies Inc.
# All Rights Reserved.
#
# This file is a property of Visual Collaboration Technologies Inc.
# Unauthorized access, reproduction or redistribution of any kind is prohibited.
"""Environment variable management for applications."""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import pandas as pd
from pydantic import BaseModel, Field

from vcti.util.env_value import EnvValueDecoder  # Replace with your actual module path
from vcti.util.value_generated_enums import EnumValueLowerCase, auto_enum_value


class VariableType(EnumValueLowerCase):
    """Supported types for environment variable decoding.

    Types include:
    - STRING: Raw string
    - FLAG: Boolean-like values (true/false)
    - INT: Integer value
    - FLOAT: Float value
    - PATH: Filesystem path
    """

    FLAG = auto_enum_value()
    STRING = auto_enum_value()
    INT = auto_enum_value()
    FLOAT = auto_enum_value()
    PATH = auto_enum_value()


DefaultValueType = Union[str, int, float, bool, Path]
ValueType = Optional[DefaultValueType]


class Variable(BaseModel):
    """Represents a single environment variable, including its metadata and resolved value.

    Attributes:
        id (str): Unique key identifier for the variable (not prefixed).
        type (VariableType): Type of the variable used for decoding.
        default_value (Any): Fallback value used if the variable is not set at runtime.
        name (Optional[str]): Full environment variable name with prefix.
        payload (Optional[str]): Raw value as fetched from the OS environment.
        value (Optional[Any]): Decoded value based on the type.
    """

    id: str = Field(
        ...,
        description="Variable identifier",
    )
    type: VariableType = Field(
        ...,
        description="Variable type",
    )
    default_value: DefaultValueType = Field(
        ...,
        alias="default",
        description="Value to be used if not specified during runtime",
    )

    # Computed fields
    name: Optional[str] = Field(
        None,
        description="Name of the environment variable",
    )
    payload: Optional[str] = Field(
        None,
        description="Raw string value fetched from the runtime environment",
    )
    value: ValueType = Field(
        None,
        description="Decoded runtime value of the variable",
    )

    def compute(self, prefix: str):
        """Evaluate variable name, fetch the payload, and decode the final value.

        Args:
            prefix (str): Environment variable prefix string.
        """
        self.name = f"{prefix}{self.id.upper()}"
        self.payload = os.getenv(self.name)
        self.value = self._decode()

    def _decode(self) -> Any:
        """Decode the payload based on its type and return its value.

        Returns:
            The decoded Python value or the default if unset or invalid.

        Raises:
            ValueError: If the variable type is not supported.
        """
        decoder = {
            VariableType.STRING: EnvValueDecoder.get_string,
            VariableType.FLAG: EnvValueDecoder.get_flag,
            VariableType.INT: EnvValueDecoder.get_number,
            VariableType.FLOAT: EnvValueDecoder.get_float,
            VariableType.PATH: EnvValueDecoder.get_path,
        }.get(self.type)

        if decoder:
            return decoder(self.name, default=self.default_value)
        raise ValueError(f"Unsupported variable type: {self.type}")


class AppEnvironment:
    """Environment manager that reads, decodes, and stores variable values during the initialization.

    Attributes:
        prefix (str): Environment variable prefix to prepend to variable IDs.
        _variables (Dict[str, Variable]): Internal map from variable key to variable object.
    """

    def __init__(self, variables: List[Variable], prefix: str = ""):
        """Initialize and evaluate application variables.

        Args:
            variables (List[Variable]): List of Variable objects to manage.
            prefix (str): Environment variable prefix.
        """
        self.prefix = prefix
        self._variables: Dict[str, Variable] = {var.id: var for var in variables}
        for var in self._variables.values():
            var.compute(self.prefix)

    def get(self, key: str) -> ValueType:
        """Return the variable value.

        Args:
            key (str): Variable identifier

        Returns:
            VariableType: Variable value

        Raises:
            KeyError: If the variable is in the application variables list.
        """
        return self._variables[key].value

    def has_variable(self, key: str) -> bool:
        """Check if a variable exists in the environment.

        Args:
            key (str): Variable identifier

        Returns:
            bool: True if the key is an Application variable, False otherwise
        """

        return key in self._variables

    def variable_info(self, key: str) -> Dict[str, Any]:
        """Get information of a specific variable.

        Args:
            key (str): Variable identifier

        Returns:
           dict: Variable metadata dictionary
        """
        return self._variables[key].model_dump()

    def list_variables(self) -> List[Dict[str, Any]]:
        """Return information of all application variables.

        Returns:
            List[dict]: Metadata for all variables
        """
        return [var.model_dump() for var in self._variables.values()]

    def as_json(self) -> str:
        """Render variable metadata as a formatted JSON string.

        Returns:
            str: JSON representation of metadata
        """
        return json.dumps(self.list_variables(), indent=2)

    def as_csv(self) -> str:
        """Render variable metadata as a CSV string.

        Returns:
            str: CSV content as string
        """
        df = pd.DataFrame(self.list_variables())
        return df.to_csv(index=False)

    def as_markdown(self) -> str:
        """Render variable metadata as a markdown-formatted table.

        Returns:
            str: Markdown table string
        """
        df = pd.DataFrame(self.list_variables())
        return df.to_markdown(index=False)
