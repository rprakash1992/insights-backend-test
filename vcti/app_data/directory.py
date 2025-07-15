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
- Environment variable configuration
- Platform-specific directory locations
- Context management for safe directory operations

Example Usage:
    # Basic usage with default configuration
    app_dir = AppDataDir()
    print(f"Data directory: {app_dir.path}")
    
    # Using context manager
    with AppDataDir().context() as dir_ctx:
        # All operations will be relative to the app data directory
        (dir_ctx.path / "config.json").write_text('{"key": "value"}')
    
    # Custom base directory
    custom_dir = AppDataDir(base_directory="/custom/path")
    print(f"Custom directory: {custom_dir.path}")
"""

from contextlib import contextmanager
import getpass
import logging
import os
from pathlib import Path
import platformdirs
from typing import Iterator, Optional, Union

from vcti.util.config_value import ConfigValue, ConfigVariable

class AppDataDir:
    def __init__(
        self,
        *,  # Force keyword arguments
        base_directory: Optional[Union[Path, str]] = None,
        env_prefix: Optional[str] = None,
    ):
        """
        Initialize the application data directory manager.

        Args:
            base_directory: Optional root directory for the application data.
                If provided as a string, will be converted to Path.
                If only a name is provided, will use platform-specific user data directory.
                If None, will determine directory from app name configuration.
            env_prefix: Optional prefix for environment variables used in configuration.
                If None, no prefix will be used.

        Examples:
            >>> # Using platform default location
            >>> app_dir = AppDataDir()
            
            >>> # Custom directory name in platform location
            >>> app_dir = AppDataDir(base_directory="my_app_data")
            
            >>> # Full custom path
            >>> app_dir = AppDataDir(base_directory="/custom/path/to/data")
        """
        self._dir_path = None

        if base_directory is not None:
            self._dir_path = Path(base_directory) if isinstance(base_directory, str) else base_directory
            if len(self._dir_path.parts) > 1:
                # Has path components - use as full base directory
                return

        # Determine application parameters from from configuration
        env_prefix = env_prefix or ""
        config = ConfigValue(env_prefix)

        if self._dir_path is not None:
            app_author = str(self._dir_path)
        else:
            app_author = config.value(ConfigVariable.APP_AUTHOR)

        app_name = config.value(ConfigVariable.APP_NAME)
        self._dir_path = platformdirs.user_data_path(app_name, app_author)

    @property
    def path(self) -> Optional[Path]:
        """
        Get the path to the application data directory.

        Returns:
            Path object representing the application data directory, or None if not initialized.

        Example:
            >>> app_dir = AppDataDir()
            >>> config_path = app_dir.path / "config.json"
            >>> config_path.write_text('{"key": "value"}')
        """
        return self._dir_path

    @contextmanager
    def context(self) -> Iterator["AppDataDir"]:
        """
        Context manager for application data directory operations.

        Creates the directory if needed and changes working directory to it for the context duration.

        Yields:
            The current AppDataDir instance for method chaining.

        Raises:
            RuntimeError: If directory creation fails or if directory path is invalid.
            OSError: If directory operations fail.

        Examples:
            Basic usage:
            >>> with AppDataDir().context() as dir_ctx:
            ...     # Create files relative to app directory
            ...     (dir_ctx.path / "data.txt").write_text("example")

            Error handling:
            >>> try:
            ...     with AppDataDir(base_directory="/invalid/path").context() as dir_ctx:
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
            logging.debug('Entering application directory context: "%s"', self._dir_path)

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