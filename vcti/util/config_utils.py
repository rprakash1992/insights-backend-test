#!/usr/bin/env python

# Copyright (C) 2018 Visual Collaboration Technologies Inc.
# All Rights Reserved.
#
# This file is a property of Visual Collaboration Technologies Inc.
# Unauthorized access, reproduction or redistribution of any kind is prohibited.
"""Defines the Configuration Utility methods."""

from typing import Optional, TypeVar

ValueType = TypeVar("ValueType")


class ConfigUtils:
    """
    Configuration Utility methods for resolving configuration values.
    """

    @staticmethod
    def get_value(
        direct_value: Optional[ValueType],
        env_value: Optional[str],
        default_value: Optional[ValueType],
    ) -> Optional[ValueType]:
        """
        Resolve a configuration value from multiple sources with proper error handling.

        Args:
            direct_value: Value passed directly to constructor
            env_value: Value from environment variable
            default_value: Default constructed value

        Returns:
            Resolved setting value

        Raises:
            ValueError: If setting cannot be resolved from any source
        """
        if direct_value is not None:
            return direct_value
        if env_value is not None:
            return env_value
        return default_value
