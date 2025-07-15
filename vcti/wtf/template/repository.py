#!/usr/bin/env python

# Copyright (C) 2018 Visual Collaboration Technologies Inc.
# All Rights Reserved.
#
# This file is a property of Visual Collaboration Technologies Inc.
# Unauthorized access, reproduction or redistribution of any kind is prohibited.
"""
TemplateRepository provides methods to manage template repositories.
"""

import os
from pathlib import Path
from typing import List, Optional, Union
from fastapi import UploadFile

from vcti.wtf.env_vars import EnvVar
from vcti.util.git_repository_manager import GitRepositoryManager
from vcti.archive.zip_extractor import ZipExtractor

from .template import Template
from .utils import create_unique_str


DEFAULT_TEMPLATES_DIR_NAME = "templates"


class TemplatesRepository:
    def __init__(
        self,
        local_repo_path: Optional[Union[str, Path]] = None,
        local_repo_env_var: str = EnvVar.DEFAULT_LOCAL_TEMPLATES_PATH,
        parent_dir: Optional[Union[str, Path]] = None,
        templates_dir_name: str = DEFAULT_TEMPLATES_DIR_NAME,
    ) -> None:
        """
        Initialize the template repository manager with local path configuration.
    
        The local repository path is determined by the following precedence:
        1. Explicit local_repo_path argument
        2. Environment variable specified by local_repo_env_var
        3. Derived from parent_dir/templates_dir_name
    
        Args:
            local_repo_path: Explicit path to the local repository
            local_repo_env_var: Environment variable containing local repo path
            parent_dir: Fallback parent directory if no path specified
            templates_dir_name: Directory name for templates if deriving path
        
        Raises:
            ValueError: If no valid local path could be determined
        """
        repo_path = None
        if local_repo_path:
            repo_path = Path(local_repo_path).expanduser().resolve()
        elif local_repo_env_var is not None:
            env_value = os.getenv(local_repo_env_var)
            if env_value is not None:
                repo_path = Path(env_value).expanduser().resolve()

        if not repo_path:
            parent_dir = Path(parent_dir).expanduser() if parent_dir else Path.cwd()
            repo_path = parent_dir / templates_dir_name
    
        if not repo_path:
            raise ValueError(
                "Could not determine local repository path. "
                "Must provide either: "
                "1) local_repo_path, "
                "2) valid local_repo_env_var, or "
                "3) parent_dir"
            )

        self._repo_manager = GitRepositoryManager(repo_path)

    @property
    def directory_path(self) -> Path:
        return self._repo_manager.directory_path

    def initialize(self):
        """
        Clone a remote repository to the configured local path if local repository doesn't exist.
        """
        if not self.directory_path.exists():
            self.create_directory()

    def create_directory(
        self,
        remote_repo_url: Optional[str] = None,
        remote_repo_env_var: str = EnvVar.DEFAULT_REMOTE_TEMPLATES_REPO,
    ) -> Path:
        """
        Clone a remote repository to the configured local path.
    
        Args:
            remote_repo_url: Direct URL to the remote repository
            remote_repo_env_var: Environment variable containing remote URL
        
        Returns:
            Path: Path to the cloned local repository
        
        Raises:
            ValueError: If remote URL is not specified or local path exists
            git.exc.GitCommandError: If clone operation fails
        
        Example:
            >>> manager = TemplateRepositoryManager(local_repo_path="/path/to/repo")
            >>> manager.create_repository("https://github.com/example/repo.git")
        """
        remote_repo_url = remote_repo_url or os.getenv(remote_repo_env_var)
    
        if not remote_repo_url:
            raise ValueError(
                "Remote repository URL must be specified either directly "
                f"or through {remote_repo_env_var} environment variable"
            )
        
        self._repo_manager.create_from_remote(remote_repo_url)
        return self.directory_path
    
    def get_template(self, template_id: str) -> Template:
        """Returns a Template object for the specified ID"""
        template_path = self.directory_path / template_id
        if not template_path.exists():
            raise FileNotFoundError(f"Template not found: {template_id}")
        return Template(template_path, self.directory_path)

    def create_template(self, archive: UploadFile) -> Template:
        """Creates a new template from an uploaded archive"""
        base_name = ""
        if archive.filename:
            base_name = Path(archive.filename).stem
        template_id = base_name
        
        if (self.directory_path / template_id).exists():
            template_id = f"{base_name}_{create_unique_str()}"
        
        target_dir = self.directory_path / template_id
        target_dir.mkdir(parents=True, exist_ok=False)
        
        zip_extractor = ZipExtractor(archive, target_dir)
        zip_extractor.extract_using_bytesio()

        return Template(target_dir, self.directory_path)

    def list_templates(self) -> List['Template']:
        """
        Retrieve all valid templates in the repository.
        
        Returns:
            List[Template]: List of initialized Template objects for valid templates.
            Only includes directories that successfully parse as templates.
            
        Note:
            Silently skips directories that don't meet template requirements.
            Logs warnings for problematic templates.
            
        Example:
            >>> repo = TemplateRepository("/path/to/repo")
            >>> templates = repo.list_templates()
            >>> [t.name for t in templates]
            ['static-analysis-template', 'modal_analysis-template']
        """
        valid_templates = []
        for template_dir in self.directory_path.iterdir():
            if template_dir.is_dir():
                template = Template(template_dir, self.directory_path)
                if template.has_info_file(): # The subdirectory is a template folder
                    valid_templates.append(template)
        return valid_templates
