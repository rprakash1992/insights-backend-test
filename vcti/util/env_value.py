#!/usr/bin/env python

# Copyright (C) 2018 Visual Collaboration Technologies Inc.
# All Rights Reserved.
#
# This file is a property of Visual Collaboration Technologies Inc.
# Unauthorized access, reproduction or redistribution of any kind is prohibited.
"""
Environment variable handling with type-safe decoding and validation.
"""

import json
import os
from pathlib import Path
from typing import Any, List, Optional, Set, Union


class EnvValueDecoder:
    """Decodes environment variables into Python types with validation."""

    DEFAULT_TRUE_VALUES: Set[str] = {"1", "true", "yes", "on", "enabled"}
    DEFAULT_FALSE_VALUES: Set[str] = {"0", "false", "no", "off", "disabled"}

    @staticmethod
    def get_payload(var: str) -> Optional[str]:
        """
        Retrieve the raw string value of an environment variable.

        Args:
            var: Name of the environment variable

        Returns:
            The variable value as string or None if not set
        """
        return os.getenv(var)

    @staticmethod
    def get_flag(
        var: str,
        *,
        true_values: Optional[Union[Set[str], List[str]]] = None,
        false_values: Optional[Union[Set[str], List[str]]] = None,
        default: Optional[bool] = None,
    ) -> Optional[bool]:
        """
        Decode a boolean from an environment variable.

        Args:
            var: Environment variable name
            true_values: Custom set of values considered True
            false_values: Custom set of values considered False
            default: Fallback value if variable not set or invalid

        Returns:
            Decoded boolean or default if provided

        Raises:
            ValueError: If value doesn't match true/false sets and no default
        """
        value = EnvValueDecoder.get_payload(var)
        if value is None:
            return default

        value = value.strip().lower()
        true_set = (
            set(true_values) if true_values else EnvValueDecoder.DEFAULT_TRUE_VALUES
        )
        false_set = (
            set(false_values) if false_values else EnvValueDecoder.DEFAULT_FALSE_VALUES
        )

        if value in true_set:
            return True
        if value in false_set:
            return False
        if default is not None:
            return default

        raise ValueError(
            f"Invalid boolean value '{value}' for variable '{var}'. "
            f"Valid values: {sorted(true_set | false_set)}"
        )

    @staticmethod
    def get_number(var: str, default: Optional[int] = None) -> Optional[int]:
        """
        Decode an integer from an environment variable.

        Args:
            var: Environment variable name
            default: Fallback value if variable not set or invalid

        Returns:
            Decoded integer or default if provided

        Raises:
            ValueError: If default is not an integer or None
        """
        if default is not None and not isinstance(default, int):
            raise ValueError("Default must be integer or None")

        value = EnvValueDecoder.get_payload(var)
        if value is None or value.strip() == "":
            return default

        try:
            return int(value.strip())
        except ValueError:
            return default

    @staticmethod
    def get_string(var: str, default: Optional[str] = None) -> Optional[str]:
        """
        Decode a string from an environment variable.

        Args:
            var: Environment variable name
            default: Fallback value if variable not set

        Returns:
            Stripped string value or default if provided

        Raises:
            ValueError: If default is not string or None
        """
        if default is not None and not isinstance(default, str):
            raise ValueError("Default must be string or None")

        value = EnvValueDecoder.get_payload(var)
        return value.strip() if value else default

    @staticmethod
    def get_file_path(
        var: str, default: Optional[Union[str, Path]] = None
    ) -> Optional[Path]:
        """
        Decode a file path from an environment variable.

        Args:
            var: Environment variable name
            default: Fallback path if variable not set

        Returns:
            Path object or default if provided

        Raises:
            ValueError: If default is not Path/str or None
        """
        if default is not None and not isinstance(default, (str, Path)):
            raise ValueError("Default must be Path/str or None")

        value = EnvValueDecoder.get_payload(var)
        if value is not None:
            return Path(value.strip())
        if default is not None:
            return default if isinstance(default, Path) else Path(default)
        return default

    @staticmethod
    def get_float(var: str, default: Optional[float] = None) -> Optional[float]:
        """
        Decode a float from an environment variable.

        Args:
            var: Environment variable name
            default: Fallback value if variable not set or invalid

        Returns:
            Decoded float or default if provided

        Raises:
            ValueError: If default is not numeric or None
        """
        if default is not None and not isinstance(default, (float, int)):
            raise ValueError("Default must be float/int or None")

        value = EnvValueDecoder.get_payload(var)
        if value is None or value.strip() == "":
            return default

        try:
            return float(value.strip())
        except ValueError:
            return default


class EnvJsonValueDecoder(EnvValueDecoder):
    """Decodes JSON-encoded environment variables into Python objects."""

    @staticmethod
    def get_object(var: str, default: Optional[Any] = None) -> Optional[Any]:
        """
        Decode a JSON object from an environment variable.

        Args:
            var: Environment variable name
            default: Fallback value if variable not set or invalid

        Returns:
            Decoded Python object or default if invalid
        """
        value = EnvValueDecoder.get_payload(var)
        if not value:
            return default

        try:
            return json.loads(value.strip())
        except (json.JSONDecodeError, TypeError):
            return default
