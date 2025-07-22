#!/usr/bin/env python

# Copyright (C) 2018 Visual Collaboration Technologies Inc.
# All Rights Reserved.
#
# This file is a property of Visual Collaboration Technologies Inc.
# Unauthorized access, reproduction or redistribution of any kind is prohibited.
"""
Application directory management with configurable policies.

Provides a class for managing application data directories with support for:
- Custom base directories
- Context management for safe directory operations

Example Usage:
    # Usage as context manager
    with AppDataDirectory("~/.config/my_app").context() as app_data_ctx:
        # All operations will be relative to the app data directory
        print(f"Custom directory: {app_data_ctx.path}")
        (app_data_ctx.path / "config.json").write_text('{"key": "value"}')
"""

import logging
import os
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, Optional, Union


class AppDataDirectory:
    def __init__(self, base_dir: Union[Path, str]):
        """
        Initialize the application data directory manager.

        Args:
            base_dir: Root directory for the application data.
                If provided as a string, will be converted to Path.

        Examples:
            >>> app_dir = AppDataDirectory("/path/to/app/data")
        """
        self._dir_path = Path(base_dir) if isinstance(base_dir, str) else base_dir

    @property
    def path(self) -> Optional[Path]:
        """
        Get the path to the application data directory.

        Returns:
            Path object representing the application data directory.

        Example:
            >>> app_dir = AppDataDirectory("~/.config/my_app")
            >>> config_path = app_dir.path / "config.json"
        """
        return self._dir_path

    @contextmanager
    def context(self) -> Iterator["AppDataDirectory"]:
        """
        Context manager for application data directory operations.

        Creates the directory if needed and changes working directory to it for the context duration.

        Yields:
            The current AppDataDirectory instance for method chaining.

        Raises:
            RuntimeError: If directory creation fails or if directory path is invalid.
            OSError: If directory operations fail.

        Examples:
            Basic usage:
            >>> with AppDataDirectory("~/.config/my_app").context() as dir_ctx:
            ...     # Create files relative to app directory
            ...     (dir_ctx.path / "data.txt").write_text("example")

            Error handling:
            >>> try:
            ...     with AppDataDirectory("/invalid/path").context() as dir_ctx:
            ...         pass
            ... except RuntimeError as e:
            ...     print(f"Failed: {e}")
        """
        original_cwd = Path.cwd()
        if not self._dir_path:
            raise RuntimeError("Invalid application data directory")

        try:
            # Ensure the base directory exists
            self._dir_path.mkdir(parents=True, exist_ok=True)
            logging.debug(
                'Entering application directory context: "%s"', self._dir_path
            )

            # Change to application directory
            os.chdir(self._dir_path)
            logging.debug('Changed working directory to: "%s"', self._dir_path)

            yield self

        except Exception as e:
            logging.error('Application data context error: "%s"', str(e), exc_info=True)
            raise
        finally:
            # Restore original working directory
            os.chdir(original_cwd)
            logging.debug('Restored working directory to: "%s"', original_cwd)
