#!/usr/bin/env python

# Copyright (C) 2018 Visual Collaboration Technologies Inc.
# All Rights Reserved.
#
# This file is a property of Visual Collaboration Technologies Inc.
# Unauthorized access, reproduction or redistribution of any kind is prohibited.
"""
Template class provides methods to manage individual templates in a repository.
"""

from pathlib import Path
from typing import List
import shutil
import uuid

from .file_manager import TemplateFileManager
from .file_names import FileNames
from .info import TemplateInfo
from ..variable.list import Variables
from ..yaml_reader import read_model, root_locator


class Template:
    def __init__(self, template_path: Path, repo_root: Path):
        """
        Main Template class composing metadata and file operations.
        
        Args:
            template_path: Absolute path to template directory
            repo_root: Absolute path to repository root
        """
        self.path = template_path
        self.repo_root = repo_root
        self.files = TemplateFileManager(template_path, repo_root)

    @property
    def id(self) -> str:
        return self.path.name

    # Metadata operations
    def get_info_file_path(self):
        return self.path / FileNames.SOURCE_DIR / FileNames.INFO_YAML

    def get_variables_file_path(self):
        return self.path / FileNames.SOURCE_DIR / FileNames.VARIABLES_YAML

    def has_info_file(self) -> bool:
        return self.get_info_file_path().exists()

    def get_info(self) -> TemplateInfo:
        """Retrieves parsed template information"""
        info_file_path = self.get_info_file_path()
        if not info_file_path.exists():
            raise FileNotFoundError(f"Info file not found at {info_file_path}")
        return read_model(info_file_path, root_locator, TemplateInfo)

    def get_variables(self) -> Variables:
        """Retrieves template variables configuration"""
        variables_file_path = self.get_variables_file_path()
        if not variables_file_path.exists():
            return Variables(root=[])
        try:
            return read_model(variables_file_path, root_locator, Variables)
        except Exception as e:
            raise RuntimeError(f"Failed to parse variables: {str(e)}")

    # File operations
    def download(self):
        return self.files.download_directory(file_name=f'{self.id}.vis')

    def upload_file(self, relative_path: List[str], file):
        return self.files.upload_file(relative_path, file)

    def get_file_tree(self, relative_path: List[str] = []):
        return self.files.get_file_tree(relative_path)

    # Template lifecycle operations
    def duplicate(self) -> 'Template':
        """Creates copy of template with new ID"""
        new_id = f"{self.id}_copy_{uuid.uuid4().hex[:8]}"
        new_path = self.path.parent / new_id
        if new_path.exists():
            raise FileExistsError(
                f"Cannot duplicate template - target path already exists: {new_path}"
            )

        shutil.copytree(self.path, new_path)
        return Template(new_path, self.repo_root)

    def rename(self, new_id: str) -> 'Template':
        """Renames the template directory"""
        if not new_id:
            raise ValueError("New template ID cannot be empty")

        new_path = self.path.parent / new_id
        if new_path.exists():
            raise FileExistsError(
                f"Cannot rename template - target path already exists: {new_path}"
            )

        shutil.move(self.path, new_path)
        self.path = new_path
        # Update managers with new path
        self.files = TemplateFileManager(new_path, self.repo_root)
        return self

    def delete(self):
        """Deletes the template directory"""
        shutil.rmtree(self.path)