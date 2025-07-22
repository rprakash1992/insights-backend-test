#!/usr/bin/env python

# Copyright (C) 2018 Visual Collaboration Technologies Inc.
# All Rights Reserved.
#
# This file is a property of Visual Collaboration Technologies Inc.
# Unauthorized access, reproduction or redistribution of any kind is prohibited.
"""Utility functions for handling file and folder paths."""

import re
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


def resolve_path(path: Union[Path, str], base_dir: Union[Path, str]) -> Path:
    """
    Resolves a path relative to a base directory, handling both absolute and relative paths.

    Args:
        path (Union[Path, str]): The path to resolve (absolute or relative)
        base_dir (Union[Path, str]): The base directory for relative path resolution

    Returns:
        Path: The fully resolved absolute path

    Raises:
        FileNotFoundError: If the base_dir does not exist
        NotADirectoryError: If base_dir is not a directory
    """
    path = Path(path) if isinstance(path, str) else path
    base_dir = Path(base_dir) if isinstance(base_dir, str) else base_dir

    # Resolve the path
    if not path.is_absolute():
        validate_folder_access(base_dir)
        path = base_dir / path

    return path.resolve()


class FileNameValidator:
    """
    Validates basic file or folder names based on common restrictions.

    Rules:
    - Must not be "." or ".."
    - Must not be empty or whitespace only
    - Must not contain illegal characters: / \\ : * ? " < > |

    This class is useful for validating user-supplied names for files or
    directories before creating them on the filesystem.

    Example:
        >>> FileNameValidator.is_valid("file.txt")        # Returns True
        >>> FileNameValidator.is_valid("invalid|file")    # Returns False
        >>> FileNameValidator.validate("data.json")       # OK
        >>> FileNameValidator.validate("bad/name")        # Raises ValueError
    """

    INVALID_CHARS = r'<>:"/\\|?*'
    INVALID_PATTERN = re.compile(rf"[{re.escape(INVALID_CHARS)}]")
    RESERVED_NAMES = {".", ".."}

    @classmethod
    def is_valid(cls, name: str) -> bool:
        """
        Returns whether the given file or folder name is valid.

        Args:
            name (str): Name to check.

        Returns:
            bool: True if valid, False otherwise.
        """
        if not name or name.strip() == "":
            return False

        if name in cls.RESERVED_NAMES:
            return False

        if cls.INVALID_PATTERN.search(name):
            return False

        return True

    @classmethod
    def validate(cls, name: str) -> None:
        """
        Validates the given file or folder name.

        Args:
            name (str): The filename to validate.

        Raises:
            ValueError: If the name is reserved, empty, or contains illegal characters.
        """
        if not cls.is_valid(name):
            raise ValueError(f"Invalid file or directory name: {name!r}")
