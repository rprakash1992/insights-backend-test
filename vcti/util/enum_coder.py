#!/usr/bin/env python

# Copyright (C) 2018 Visual Collaboration Technologies Inc.
# All Rights Reserved.
#
# Thils file is a property of Visual Collaboration Technologis Inc.
# Unauthorized access, reproduction or redistribution of any kind is prohibited.
"""Enhanced Enum utilities for flexible serialization with configurable string mappings."""

from enum import Enum
from typing import (Any, Callable, Dict, List, Literal, Optional, Tuple, Type,
                    TypeVar)

E = TypeVar('E', bound=Enum)

class EnumCoder:
    """
    Provides flexible serialization/deserialization for Enums with configurable string mappings.

    Example:
        class Color(Enum):
            RED = 1
            GREEN = 2

        # Create serializer with lowercase mapping
        color_coder = EnumCoder(
            Color,
            value_generator=lambda enum_var: enum_var.name.lower(),
            default=Color.RED
        )

        # Serialize/Encode
        color_coder.encode(Color.RED)  # "red"

        # Deserialize/Decode
        color_coder.decode("green")  # Color.GREEN
    """

    def __init__(
        self,
        enum_class: Type[E],
        value_generator: Callable[[E], str] = lambda enum_var: enum_var.name,
        default: Optional[E] = None,
    ):
        """
        Initialize the serializer.

        Args:
            enum_class: The Enum class to serialize
            value_generator: Function that converts enums to string values
            default: Default enum value for this serializer
        """
        self.enum_class = enum_class
        self.value_generator = value_generator

        # Generate mappings
        self._enum_to_string: Dict[E, str] = {
            member: value_generator(member) for member in enum_class
        }
        self._string_to_enum: Dict[str, E] = {v: k for k, v in self._enum_to_string.items()}

        # Pre-compute stringified default
        self._default = self._enum_to_string.get(default) if default else None

    @property
    def default(self) -> Optional[str]:
        """The string representation of the default enum value (None if no default set)."""
        return self._default

    @property
    def tuple(self) -> Tuple[str, ...]:
        """All possible string values for this enum."""
        return tuple(self._enum_to_string.values())

    @property
    def list(self) -> List[str]:
        """List of all possible string values."""
        return list(self.tuple)

    @property
    def Literal(self) -> Literal:
        """Literal type containing all possible string values."""
        return Literal[*self.tuple]

    def encode(self, enum_value: E) -> str:
        """Convert enum to its string representation."""
        return self._enum_to_string[enum_value]

    def decode(self, string_value: str) -> E:
        """
        Convert string back to enum value.

        Raises:
            ValueError: If string_value doesn't match any enum value
        """
        try:
            return self._string_to_enum[string_value]
        except KeyError:
            raise ValueError(
                f"'{string_value}' is not a valid representation. "
                f"Valid values: {self.tuple}"
            )

    def get_mapping_info(self) -> Dict[str, Any]:
        """Get complete mapping information as a dictionary."""
        return {
            'enum_class': self.enum_class.__name__,
            'values': self.tuple,
            'default': self.default,
            'mapping': {e.name: self.encode(e) for e in self.enum_class}
        }
