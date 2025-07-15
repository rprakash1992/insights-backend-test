#!/usr/bin/env python

# Copyright (C) 2018 Visual Collaboration Technologies Inc.
# All Rights Reserved.
#
# This file is a property of Visual Collaboration Technologies Inc.
# Unauthorized access, reproduction or redistribution of any kind is prohibited.
"""Defines the variable types for workflow parameters."""

from vcti.util.value_generated_enums import EnumValueLowerCase, auto_enum_value


class VariableType(EnumValueLowerCase):
    """
    Enum representing the types of variables supported in the workflow.

    Attributes:
        AUTO_DETECT: Automatically detects the type.
        INT: Integer type.
        FLOAT: Floating-point type.
        BOOL: Boolean type.
        STRING: String type.
        INPUT_FILE_PATH: Path to an existing input file.
        OUTPUT_FILE_PATH: Path for an output file.
        INPUT_FOLDER_PATH: Path to an existing input directory.
        OUTPUT_FOLDER_PATH: Path for an output directory.
        OBJECT: Generic object.
        NUMPY_ARRAY: NumPy array.
    """

    AUTO_DETECT = "auto-detect"
    INT = auto_enum_value()
    FLOAT = auto_enum_value()
    BOOL = auto_enum_value()
    STRING = auto_enum_value()
    INPUT_FILE_PATH = auto_enum_value()
    OUTPUT_FILE_PATH = auto_enum_value()
    INPUT_FOLDER_PATH = auto_enum_value()
    OUTPUT_FOLDER_PATH = auto_enum_value()
    OBJECT = auto_enum_value()
    NUMPY_ARRAY = auto_enum_value()
