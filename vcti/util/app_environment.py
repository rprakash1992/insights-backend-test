#!/usr/bin/env python

# Copyright (C) 2018 Visual Collaboration Technologies Inc.
# All Rights Reserved.
#
# This file is a property of Visual Collaboration Technologies Inc.
# Unauthorized access, reproduction or redistribution of any kind is prohibited.
"""Environment variable management for applications."""

import os
from pathlib import Path
from typing import Any, ClassVar, Dict, Optional, Type, TypeVar, Union

from vcti.util.env_value import EnvValueDecoder
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


DECODER_DICT = {
    VariableType.STRING: EnvValueDecoder.get_string,
    VariableType.FLAG: EnvValueDecoder.get_flag,
    VariableType.INT: EnvValueDecoder.get_number,
    VariableType.FLOAT: EnvValueDecoder.get_float,
    VariableType.PATH: EnvValueDecoder.get_path,
}


class Variable:
    def __init__(self, type: VariableType, default: DefaultValueType):
        self.type = type
        self.default_value = default

        self.env_name: Optional[str] = None
        self.env_value: Optional[str] = None
        self.value: ValueType = None

    def resolve(self, env_name: str) -> None:
        """Evaluate variable name, fetch the payload, and decode the final value.

        Args:
            env_name (str): Full environment variable name
        """
        self.env_name = env_name
        self.env_value = os.getenv(self.env_name)

        decoder = DECODER_DICT.get(self.type)
        if decoder is None:
            raise ValueError(f"Unsupported variable type: {self.type}")

        self.value = decoder(self.env_name, default=self.default_value)

    def __repr__(self):
        return f"<Variable(name={self.env_name}, value={self.value!r})>"


T = TypeVar("T", bound="AppEnvironmentBase")  # Base class for all environment classes


class AppEnvironmentMeta(type):
    def __new__(
        mcs: Type[type], name: str, bases: tuple, namespace: Dict[str, Any]
    ) -> T:
        prefix = namespace.get("ENV_PREFIX", "")
        variables: Dict[str, Variable] = {}

        for attr, val in namespace.items():
            if isinstance(val, Variable):
                val.resolve(f"{prefix}{attr.upper()}")
                variables[attr] = val

        cls = super().__new__(mcs, name, bases, namespace)
        cls._variables = variables  # type: ignore
        return cls


class AppEnvironmentBase(metaclass=AppEnvironmentMeta):
    """Base class for all environment classes using AppEnvironmentMeta."""

    pass
