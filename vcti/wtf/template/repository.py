#!/usr/bin/env python

# Copyright (C) 2018 Visual Collaboration Technologies Inc.
# All Rights Reserved.
#
# This file is a property of Visual Collaboration Technologies Inc.
# Unauthorized access, reproduction or redistribution of any kind is prohibited.
"""
TemplateRepository provides methods to manage template repositories.
"""

from pathlib import Path
from typing import List, Optional, Union

from fastapi import UploadFile

from vcti.archive.zip_extractor import ZipExtractor
from vcti.util.git_repository_manager import GitRepositoryManager
from vcti.util.short_uid import ShortUID

from .template import Template


class TemplatesRepository:
    def __init__(
        self,
        local_repo_path: Union[str, Path],
        remote_repo_url: Optional[str] = None,
    ) -> None:
        """
        Manages a local template repository.
        If the local repository doesn't exist, it is cloned from a remote source.

        Args:
            local_repo_path (Union[str, Path]): Path to the local repository.
            remote_repo_url (Optional[str]): Remote Git repository URL.

        Raises:
            ValueError: If the local path is not provided or the remote is required but missing.
        """
        if not local_repo_path:
            raise ValueError("Invalid local repository path. ")

        self._repo_manager = GitRepositoryManager(
            Path(local_repo_path).expanduser().resolve()
        )

        if not self._repo_manager.directory_path.exists():
            if not remote_repo_url:
                raise ValueError(
                    "Local repository path does not exist and no remote repository URL was provided."
                )
            self._repo_manager.create_from_remote(remote_repo_url)

    @property
    def directory_path(self) -> Path:
        """Returns the path to the local repository."""
        return self._repo_manager.directory_path

    def get_template_path(
        self,
        template_id: str,
        is_new: bool = False,
    ) -> Path:
        """
        Resolves the path to a template given its ID.

        Args:
            template_id (str): The ID (i.e., folder name) of the template.
            is_new (bool): If True, does not check if the path exists.

        Returns:
            Path: Path to the template directory.

        Raises:
            FileNotFoundError: If the template does not exist and is_new is False.
        """
        template_path = (self.directory_path / template_id).resolve()

        if not is_new and not template_path.exists():
            raise FileNotFoundError(f"Template not found: {template_id}")

        return template_path

    def get_template(self, template_id: str) -> Template:
        """
        Returns a Template instance for the given template ID.

        Args:
            template_id (str): ID of the template.

        Returns:
            Template: Initialized template object.
        """
        return Template(self.get_template_path(template_id))

    def create_template(
        self,
        archive: UploadFile,
        prefix: str = "template",
    ) -> Template:
        """
        Creates a new template from an uploaded ZIP archive.

        Args:
            archive (UploadFile): The uploaded ZIP archive.
            prefix (str): Prefix for the new template ID.

        Returns:
            Template: Newly created Template instance.
        """
        base_name = Path(archive.filename).stem if archive.filename else prefix
        template_id = f"{base_name}_{ShortUID.quick()}"

        template_dir = self.get_template_path(template_id, is_new=True)
        template_dir.mkdir(parents=True, exist_ok=False)

        zip_extractor = ZipExtractor(archive, template_dir)
        zip_extractor.extract_using_bytesio()

        return Template(template_dir)

    def list_templates(self) -> List["Template"]:
        """
        Lists all valid templates in the local repository.
        Skips directories that are not valid templates.

        Returns:
            List[Template]: Templates that pass validation.

        Usage:
            >>> repo = TemplateRepository("/path/to/repo")
            >>> templates = repo.list_templates()
            >>> [t.name for t in templates]
            ['static-analysis-a03xb', 'modal_analysis-b04xc', ...]
        """
        templates = []

        for entry in self.directory_path.iterdir():
            if not entry.is_dir():
                continue

            template = Template(entry)
            if template.workflow_nodes.is_valid():
                templates.append(template)

        return templates
