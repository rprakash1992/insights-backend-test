#!/usr/bin/env python

# Copyright (C) 2018 Visual Collaboration Technologies Inc.
# All Rights Reserved.
#
# This file is a property of Visual Collaboration Technologies Inc.
# Unauthorized access, reproduction or redistribution of any kind is prohibited.
"""Utility class for validating file and folder names."""

import re


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
