#!/usr/bin/env python

# Copyright (C) 2018 Visual Collaboration Technologies Inc.
# All Rights Reserved.
#
# This file is a property of Visual Collaboration Technologies Inc.
# Unauthorized access, reproduction or redistribution of any kind is prohibited.
"""Utility functions for handling file and folder paths."""

from pathlib import Path
from typing import Union

from vcti.error import system_error


def abs_path(fp: Union[Path, str]) -> Path:
    """
    Converts a given file path to an absolute, resolved `Path` object.

    Args:
        fp (Union[Path, str]): The input file path.

    Returns:
        Path: The absolute resolved file path.
    """
    return Path(fp).resolve()


def validate_file_access(fp: Union[Path, str]) -> None:
    """
    Validates that the specified file path exists and is a readable file.

    Args:
        fp (Union[Path, str]): The file path to validate.

    Raises:
        FileNotFoundError: If the file does not exist.
        IsADirectoryError: If the path points to a directory instead of a file.
        PermissionError: If the file exists but is not readable.
    """
    path = Path(fp)

    if not path.exists():
        raise system_error(FileNotFoundError, path)

    if path.is_dir():
        raise system_error(IsADirectoryError, path)

    if not path.is_file():
        raise system_error(FileNotFoundError, path)

    if not path.stat().st_mode & 0o400:  # Check read permission
        raise system_error(PermissionError, path)


def validate_folder_access(fp: Union[Path, str]) -> None:
    """
    Validates that the specified folder path exists and is a directory.

    Args:
        fp (Union[Path, str]): The folder path to validate.

    Raises:
        FileNotFoundError: If the directory does not exist.
        NotADirectoryError: If the path is not a directory.
    """
    path = Path(fp)

    if not path.exists():
        raise system_error(FileNotFoundError, path)

    if not path.is_dir():
        raise system_error(NotADirectoryError, path)


def resolve_path(path: Union[Path, str], base_path: Union[Path, str]) -> Path:
    """
    Resolves a path relative to a base directory, handling both absolute and relative paths.

    Args:
        path (Union[Path, str]): The path to resolve (absolute or relative)
        base_path (Union[Path, str]): The base directory for relative path resolution

    Returns:
        Path: The fully resolved absolute path

    Raises:
        FileNotFoundError: If the base_path does not exist
        NotADirectoryError: If base_path is not a directory
    """
    if isinstance(path, Path):
        path_obj = path
    else:
        path_obj = Path(path)
    if isinstance(base_path, Path):
        base_path_obj = base_path
    else:
        base_path_obj = Path(base_path)

    # Validate base path first
    if not base_path_obj.exists():
        raise system_error(FileNotFoundError, base_path_obj)
    if not base_path_obj.is_dir():
        raise system_error(NotADirectoryError, base_path_obj)

    # Resolve the path
    if not path_obj.is_absolute():
        path_obj = base_path_obj / path_obj

    return path_obj.resolve()
