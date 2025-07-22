#!/usr/bin/env python

# Copyright (C) 2018 Visual Collaboration Technologies Inc.
# All Rights Reserved.
#
# This file is the property of Visual Collaboration Technologies Inc.
# Unauthorized access, reproduction, or redistribution of any kind is prohibited.

"""
Provides access to workflow node definitions and associated metadata within a template.
"""

from pathlib import Path
from typing import Optional

from ..variable.list import Variables
from ..yaml_reader import read_model, root_locator
from .file_names import FileNames
from .metadata import Metadata


class WorkflowNodes:
    """
    Manages workflow node structure and metadata under the 'source' directory of a template.

    Each node is represented by a subdirectory and can include:
      - meta.yaml         → Metadata about the node
      - variables.yaml    → Variables used in the node
      - steps.yaml        → Execution steps for the node

    An `.entrypoint` file inside the 'source' directory indicates the root node.
    """

    def __init__(self, path: Path):
        """
        Initialize the WorkflowNodes manager.

        Args:
            path (Path): Path to the template root directory.
        """
        self._path = path
        self._source_dir = self._path / FileNames.SOURCE_DIR
        self._runs_dir = self._path / FileNames.RUNS_DIR
        self._root_node = self._read_root_node()
        self._meta = None

    @property
    def root_node(self) -> Optional[str]:
        """Returns the root node identifier (folder name), or None if not defined."""
        return self._root_node

    def _root_node_file_path(self) -> Path:
        """Returns the path to the .entrypoint file."""
        return self._source_dir / FileNames.ROOT_NODE

    def _read_root_node(self) -> Optional[str]:
        """Reads the entrypoint file to determine the root workflow node name."""
        root_node_file = self._root_node_file_path()
        if not root_node_file.exists():
            return None

        return root_node_file.read_text(encoding="utf-8").strip()

    def is_valid(self) -> bool:
        """
        Validates the workflow node structure.

        Returns:
            bool: True if an root node is defined and its metadata file exists.
        """
        if not self._root_node:
            return False
        return self._meta_file_path(self.root_node)

    # File path access methods

    def _meta_file_path(self, node_name: str) -> Path:
        return self._source_dir / node_name / FileNames.META_YAML

    def _variables_file_path(self, node_name: str) -> Path:
        return self._source_dir / node_name / FileNames.VARIABLES_YAML

    def _steps_file_path(self, node_name: str) -> Path:
        return self._source_dir / node_name / FileNames.STEPS_YAML

    def node_metadata(self, node_name: str) -> Optional[Metadata]:
        """
        Loads and returns metadata for a specific workflow node.

        Args:
            node_name (str): Name of the workflow node (i.e., subdirectory under 'source').

        Returns:
            Optional[Metadata]: Parsed metadata model, or None if file doesn't exist.

        Raises:
            RuntimeError: If YAML parsing fails.
        """
        meta_file = self._meta_file_path(node_name)
        if not meta_file.exists():
            return None

        try:
            return read_model(meta_file, root_locator, Metadata)
        except Exception as e:
            raise RuntimeError(f'Failed to parse metadata file "{meta_file}": {str(e)}')

    def node_variables(self, node_name: str) -> Variables:
        """
        Loads and returns variables for a specific workflow node.

        Args:
            node_name (str): Name of the workflow node (i.e., subdirectory under 'source').

        Returns:
            Variables: Parsed variables model, or an empty one if file doesn't exist.

        Raises:
            RuntimeError: If YAML parsing fails.
        """
        variables_file = self._variables_file_path(node_name)
        if not variables_file.exists():
            return Variables(root=[])

        try:
            return read_model(variables_file, root_locator, Variables)
        except Exception as e:
            raise RuntimeError(
                f'Failed to parse variables file "{variables_file}": {str(e)}'
            )

    def metadata(self) -> Optional[Metadata]:
        """Returns the metadata for the root workflow node.

        Returns:
            Optional[Metadata]: Parsed metadata model for the root node, or None if not defined.
        """
        return self.node_metadata(self.root_node) if self.root_node else None

    def variables(self) -> Variables:
        """Returns the variables for the root workflow node.

        Returns:
            Variables: Parsed variables model for the root node, or an empty one if not defined.
        """
        return (
            self.node_variables(self.root_node)
            if self.root_node
            else Variables(root=[])
        )
