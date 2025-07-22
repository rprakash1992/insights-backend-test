#!/usr/bin/env python

# Copyright (C) 2018 Visual Collaboration Technologies Inc.
# All Rights Reserved.
#
# This file is a property of Visual Collaboration Technologies Inc.
# Unauthorized access, reproduction or redistribution of any kind is prohibited.
"""
Template class provides methods to manage individual templates in a repository.
"""

import shutil
from pathlib import Path

from starlette.responses import StreamingResponse

from vcti.util.path_utils import FileNameValidator, validate_folder_access

from .files import TemplateFiles
from .runs import TemplateRuns
from .utils import make_duplicate_name
from .workflow_nodes import WorkflowNodes


class Template:
    def __init__(self, template_path: Path):
        """
        Initializes a Template instance with a root path and its file operations handler.

        Args:
            template_path (Path): Absolute path to the template root directory.

        Raises:
            ValueError: If the provided path does not exist or is not a directory.
        """
        validate_folder_access(template_path)

        self.path = template_path
        self.files = TemplateFiles(template_path)
        self.workflow_nodes = WorkflowNodes(template_path)
        self.runs = TemplateRuns(template_path)

    @property
    def id(self) -> str:
        """
        Returns the template ID, which is the name of the template directory.

        Returns:
            str: Template ID derived from directory name.
        """
        return self.path.name

    def download(self) -> StreamingResponse:
        """
        Download the entire template directory as a `.vis` archive.

        Returns:
            FileResponse: A response containing the zipped archive for download.
        """
        return self.files.download_directory(download_filename=f"{self.id}.vis")

    def duplicate(self) -> "Template":
        """
        Creates a copy of the template with a new unique ID.

        Returns:
            Template: A new Template instance with the duplicated content.
        """
        while True:
            new_id = make_duplicate_name(Path(self.id))
            new_path = self.path.parent / new_id
            if not new_path.exists():
                break

        shutil.copytree(self.path, new_path)
        return Template(new_path)

    def rename(self, new_id: str) -> "Template":
        """
        Renames the template directory to a new ID.

        Args:
            new_id (str): The new template ID.

        Returns:
            Template: The current instance with updated path and state.

        Raises:
            ValueError: If new_id is empty or invalid.
            FileExistsError: If a template with new_id already exists.
        """
        new_id = new_id.strip()
        if not new_id:
            raise ValueError("New template ID cannot be empty.")

        FileNameValidator.validate(new_id)

        new_path = self.path.parent / new_id
        if new_path.exists():
            raise FileExistsError(f"Template ID '{new_id}' already exists.")

        shutil.move(self.path, new_path)
        self.path = new_path
        # Update managers with new path
        self.files = TemplateFiles(self.path)
        return self

    def delete(self) -> None:
        """
        Deletes the template directory and all its contents.
        """
        shutil.rmtree(self.path)
