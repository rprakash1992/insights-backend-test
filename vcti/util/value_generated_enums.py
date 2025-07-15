#!/usr/bin/env python

# Copyright (C) 2018 Visual Collaboration Technologies Inc.
# All Rights Reserved.
#
# Thils file is a property of Visual Collaboration Technologis Inc.
# Unauthorized access, reproduction or redistribution of any kind is prohibited.
"""Custom Enum base classes for automatic value generation using naming conventions."""

from enum import Enum
from enum import auto as auto_enum_value
from typing import Any, List, Callable

import caseconverter
import inflection


def create_enum_class(value_generator: Callable[[str], str]) -> type:
    """
    Factory function to create an Enum class with a custom value generator.

    Args:
        value_generator: A function that takes the enum member name and returns the desired value.

    Returns:
        An Enum class with the custom value generator.
    """

    class DynamicEnum(Enum):
        @staticmethod
        def _generate_next_value_(
            name: str, start: int, count: int, last_values: List[Any]
        ) -> str:
            """
            Generates the next value for an enum member using the value_generator.

            Args:
                name: The name of the enum member.
                start: The starting value (usually 1).
                count: The number of existing enum members.
                last_values: A list of the last values assigned to enum members.

            Returns:
                The generated value
            """
            return value_generator(name)

    return DynamicEnum


def enum_class_doc_string(cls: type, value: str, description: str):
    return f"""
        Enum where the value of each member is {description}

        Example:
            class ExampleEnum({cls.__class__.__name__}):
                FIRST_VALUE = auto_enum_value()
                SECOND_VALUE = auto_enum_value()

            >>> ExampleEnum.FIRST.value
            '{value}'
    """


# Create Enum classes using the factory function
EnumValueSameAsName = create_enum_class(lambda name: name)
EnumValueSameAsName.__doc__ = enum_class_doc_string(
    EnumValueSameAsName, "FIRST_VALUE", "the same as its name"
)
EnumValueLowerCase = create_enum_class(lambda name: name.lower())
EnumValueLowerCase.__doc__ = enum_class_doc_string(
    EnumValueLowerCase, "first_value", "its name converted to lower case"
)
EnumValueCamelCase = create_enum_class(caseconverter.camelcase)
EnumValueCamelCase.__doc__ = enum_class_doc_string(
    EnumValueCamelCase, "firstValue", "its name converted to Camel case"
)
EnumValuePascalCase = create_enum_class(caseconverter.pascalcase)
EnumValuePascalCase.__doc__ = enum_class_doc_string(
    EnumValuePascalCase, "FirstValue", "its name converted to Pascal case"
)
EnumValueCapitalizedPhrase = create_enum_class(inflection.titleize)
EnumValueCapitalizedPhrase.__doc__ = enum_class_doc_string(
    EnumValueCapitalizedPhrase,
    "First Value",
    "its name converted to a capitalized phrase",
)
EnumValueSpaceSeparatedLower = create_enum_class(
    lambda name: inflection.humanize(name).lower()
)
EnumValueSpaceSeparatedLower.__doc__ = enum_class_doc_string(
    EnumValueSpaceSeparatedLower,
    "first value",
    "its name converted to a space separated lowercase phrase",
)
