#!/usr/bin/env python

# Copyright (C) 2018 Visual Collaboration Technologies Inc.
# All Rights Reserved.
#
# This file is a property of Visual Collaboration Technologies Inc.
# Unauthorized access, reproduction or redistribution of any kind is prohibited.
"""Utilities for validating and resolving file identifiers relative to a base directory."""

from pathlib import Path
from typing import Optional

from .filename_validator import FileNameValidator


class FileId:
    """
    Utilities to work with file identifiers—POSIX-style relative paths
    representing files or directories inside a base directory.

    Rules for a valid file ID:
    - Must not start with "/", "./", "../"
    - Must use "/" as the path separator (POSIX format)
    - Each part must be a valid file/folder name (see FileNameValidator)

    Example:
        file_id = "scripts/setup.sh"  → base_dir / "scripts/setup.sh"

    This utility supports:
    - Validating file IDs
    - Resolving file IDs to full paths
    - Extracting file IDs from full paths
    """

    @staticmethod
    def is_valid(file_id: str) -> bool:
        """
        Check if a file ID is valid.

        Args:
            file_id (str): A relative POSIX-style file ID.

        Returns:
            bool: True if valid, False otherwise.
        """
        if not file_id or file_id.strip() == "":
            return False

        if file_id.startswith(("/", "./", "../")):
            return False

        if file_id.endswith("/") and len(file_id) > 1:
            file_id = file_id.rstrip("/")

        try:
            parts = file_id.split("/")
            return all(FileNameValidator.is_valid(part) for part in parts)
        except Exception:
            return False

    @staticmethod
    def validate(file_id: str) -> None:
        """
        Validate a file ID and raise ValueError if invalid.

        Args:
            file_id (str): File ID to validate.

        Raises:
            ValueError: If the file ID is invalid.
        """
        if not FileId.is_valid(file_id):
            raise ValueError(f"Invalid file ID: '{file_id}'")

    @staticmethod
    def resolve_path(
        file_id: Optional[str],
        base_dir: Path,
        *,
        must_exist: bool = False,
        must_be_dir: bool = False,
        must_be_file: bool = False,
    ) -> Path:
        """
        Resolve a file ID to an absolute path inside the base directory.

        Args:
            file_id (Optional[str]): Relative file ID in POSIX format. If None, returns base_dir.
            base_dir (Path): The root directory to resolve from.
            must_exist (bool): Raise FileNotFoundError if path doesn't exist.
            must_be_dir (bool): Raise NotADirectoryError if path isn't a directory.
            must_be_file (bool): Raise IsADirectoryError if path isn't a file.

        Returns:
            Path: Absolute resolved path.

        Raises:
            ValueError: If file ID is invalid.
            FileNotFoundError, NotADirectoryError, IsADirectoryError: Based on flags.
        """
        target = base_dir.joinpath(Path(file_id)) if file_id else base_dir

        # Validate file ID if provided
        if file_id:
            FileId.validate(file_id)

        if must_exist and not target.exists():
            raise FileNotFoundError(f"Path does not exist: {target}")

        if target.exists():
            if target.is_symlink():
                raise RuntimeError(f"Symbolic links are not supported: {target}")
            if must_be_dir and not target.is_dir():
                raise NotADirectoryError(f"Expected a directory: {target}")
            if must_be_file and not target.is_file():
                raise IsADirectoryError(f"Expected a file: {target}")

        return target

    @staticmethod
    def get_file_id(file_path: Path, base_dir: Path) -> str:
        """
        Get the POSIX-style file ID for a file path inside the base directory.

        Args:
            file_path (Path): The absolute or relative path to convert.
            base_dir (Path): The root directory to compute relative to.

        Returns:
            str: File ID in POSIX format.

        Raises:
            ValueError: If file_path is outside the base_dir.
        """
        try:
            rel_path = file_path.relative_to(base_dir)
        except ValueError:
            raise ValueError(
                f"Path '{file_path}' is not under base directory '{base_dir}'"
            )

        if rel_path == Path("."):
            return ""

        parts = rel_path.parts
        for part in parts:
            FileNameValidator.validate(part)

        file_id = rel_path.as_posix()

        if file_path.exists() and file_path.is_dir() and rel_path != Path("."):
            return file_id + "/"

        return file_id
