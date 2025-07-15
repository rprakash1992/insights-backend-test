#!/usr/bin/env python

# Copyright (C) 2018 Visual Collaboration Technologies Inc.
# All Rights Reserved.
#
# This file is a property of Visual Collaboration Technologies Inc.
# Unauthorized access, reproduction or redistribution of any kind is prohibited.
"""YAML file reader with support for VCollab workflow templates framework specific directives."""

from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar

import yaml
import yaml_include
from pydantic import BaseModel, ValidationError
from yaml import YAMLError

from vcti.logging import logger

from .varref import VariableReference

# Constants
DEFAULT_INCLUDE_CMDS = ["include"]


def variable_constructor(loader: yaml.FullLoader, node: yaml.Node) -> VariableReference:
    """Constructor for parsing the custom !var YAML tag."""
    var_name = node.value.strip()
    if not var_name:
        raise ValueError("Empty variable reference found in YAML.")
    return VariableReference(var_name=var_name)


def load_yaml(yaml_file_path: Path, include_cmds: Optional[List[str]] = None) -> Any:
    """
    Loads a YAML file with support for custom include directives and !var tags.

    Args:
        yaml_file_path: The path to the YAML file.
        include_cmds: A list of include command names. Defaults to ['include'].

    Returns:
        The parsed YAML data as a Python dictionary or list.

    Raises:
        FileNotFoundError: If the specified YAML file does not exist.
        yaml.YAMLError: If there is an error parsing the YAML file.
        Exception: For any other unexpected errors.
    """
    if include_cmds is None:
        include_cmds = DEFAULT_INCLUDE_CMDS

    yaml_file_path = yaml_file_path.resolve()
    if not yaml_file_path.exists():
        logger.error('YAML file not found: "%s"', yaml_file_path)
        raise FileNotFoundError(f"YAML file not found: {yaml_file_path}")

    base_dir = yaml_file_path.parent
    loader = yaml.FullLoader

    # Remove existing constructors to prevent conflicts
    for cmd in include_cmds:
        yaml_tag = f"!{cmd}"
        loader.yaml_constructors.pop(yaml_tag, None)

    # Register the include constructor
    include_constructor = yaml_include.Constructor(base_dir=base_dir)
    for cmd in include_cmds:
        yaml.add_constructor(f"!{cmd}", include_constructor, loader)

    # Register the !var constructor
    yaml.add_constructor("!var", variable_constructor, loader)

    try:
        with yaml_file_path.open("r", encoding="utf-8") as file:
            return yaml.load(file, Loader=loader)
    except yaml.YAMLError as err:
        logger.error('YAML parsing error in "%s": %s', yaml_file_path, err)
        raise
    except FileNotFoundError as err:
        logger.error('File not found: "%s"', err.filename)
        raise
    except Exception as err:
        logger.error('Unexpected error reading "%s": %s', yaml_file_path, err)
        raise


def root_locator(data: Any) -> Any:
    """Locator function that returns the entire data."""
    return data


def section_locator(section: str) -> Any:
    """Factory function to create a locator for a specific section."""

    def locator(data: Dict[str, Any]) -> Any:
        return data.get(section, None)

    return locator


# Generic type for Pydantic models
ModelType = TypeVar("ModelType", bound=BaseModel)


def read_model(
    yaml_file_path: Path,
    data_locator: Callable[[Any], Any],
    model_class: Type[ModelType],
    default_value: Any = None,
) -> ModelType:
    """
    Read and parse a YAML file into a Pydantic model.

    Args:
        yaml_file_path: Path to the YAML file.
        data_locator: Function to locate the relevant data in the YAML.
        model_class: The Pydantic model class to parse the data into.
        default_value: Default value to use if the data location failed.

    Returns:
        An instance of the specified Pydantic model.

    Raises:
        FileNotFoundError: If the YAML file does not exist.
        yaml.YAMLError: If there is an error parsing the YAML file.
        ValidationError: If the data does not match the model schema.
    """
    try:
        # Load YAML data
        yaml_data = load_yaml(yaml_file_path)
    except FileNotFoundError as err:
        logger.error('YAML file reading failed: "%s"', yaml_file_path)
        raise FileNotFoundError(
            f"The YAML file '{err.filename}' does not exist."
        ) from err
    except YAMLError as err:
        logger.error('YAML parsing error in "%s": %s', yaml_file_path, err)
        raise YAMLError(f"Error parsing YAML file '{yaml_file_path}': {err}") from err

    # Locate the model data
    model_data = data_locator(yaml_data)
    if model_data is None and default_value is not None:
        model_data = default_value

    try:
        # Parse and validate the data
        model = model_class.model_validate(model_data)
        return model
    except ValidationError as e:
        logger.error('Validation error in "%s": %s', yaml_file_path, e)
        raise
