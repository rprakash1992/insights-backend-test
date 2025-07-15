#!/usr/bin/env python

# Copyright (C) 2018 Visual Collaboration Technologies Inc.
# All Rights Reserved.
#
# This file is a property of Visual Collaboration Technologies Inc.
# Unauthorized access, reproduction or redistribution of any kind is prohibited.
"""
TemplateRepositoryManager provides methods to manage template repositories.
"""

import os
from pathlib import Path
from typing import List, Optional, Union
from git import Repo
import git.exc
from pydantic import BaseModel, Field, RootModel
from fastapi import UploadFile
import zipfile
import uuid
import time
from io import BytesIO
from starlette.responses import FileResponse, StreamingResponse
import shutil

from .info import TemplateInfo
from .file_names import FileNames
from ..yaml_reader import read_model, root_locator
from ..variable.list import Variables
from vcti.util.path_tree import PathTree, get_path_tree
from vcti.wtf.env_vars import EnvVar
from vcti.util.path_utils import validate_folder_access

DEFAULT_TEMPLATES_DIR_NAME = "templates"


class TemplateItem(BaseModel):
    id: str = Field(
        ...,
        description="Template Id. Same as the folder name.",
    )
    info: TemplateInfo = Field(
        ...,
        description="Template information including title, description and others."
    )


TemplatesList = RootModel[List[TemplateItem]]


class TemplateRepositoryManager:
    def __init__(
        self,
        remote_repo_url: Optional[str] = None,
        remote_repo_env_var: Optional[str] = EnvVar.DEFAULT_REPO,
        local_repo_path: Optional[Union[str, Path]] = None,
        local_repo_env_var: Optional[str] = None,
        default_parent_dir: Optional[Union[str, Path]] = None,
        templates_dir_name: Optional[Union[str, Path]] = DEFAULT_TEMPLATES_DIR_NAME,
    ):
        """
        Initializes the TemplateRepositoryManager with remote and local repository paths.
        
        Args:
            remote_repo_url: Direct URL to the remote repository
            remote_repo_env_var: Environment variable containing remote repo URL
            local_repo_path: Direct path to local repository
            local_repo_env_var: Environment variable containing local repo path
            
        Raises:
            ValueError: If neither local_repo_path nor local_repo_env_var is specified
        """
        self.remote_repo_url = remote_repo_url or os.getenv(remote_repo_env_var)
        
        if local_repo_path:
            self.local_repo_path = Path(local_repo_path).expanduser().resolve()
        elif local_repo_env_var and os.getenv(local_repo_env_var):
            self.local_repo_path = Path(os.getenv(local_repo_env_var)).expanduser().resolve()
        else:
            parent_dir = Path(default_parent_dir).expanduser() if default_parent_dir else Path.cwd()
            self.local_repo_path = parent_dir / templates_dir_name
        if not self.local_repo_path:
            raise ValueError(
                "Invalid arguments. "
                "Unable to identify local repository path."
            )

    def create_local_repo(self) -> Path:
        """
        Clones the remote repository to the local repository path.
        
        Returns:
            Path to the cloned local repository
            
        Raises:
            ValueError: If remote_repo_url is not set
            FileExistsError: If local repository path already exists
            RuntimeError: If clone operation fails
        """
        if not self.remote_repo_url:
            raise ValueError("Remote repository URL is not specified.")
        if self.local_repo_path.exists():
            raise FileExistsError(f"Local repository path already exists: {self.local_repo_path}")

        try:
            Repo.clone_from(self.remote_repo_url, self.local_repo_path)
            return self.local_repo_path
        except git.exc.GitCommandError as e:
            raise RuntimeError(f"Failed to clone repository: {e}")

    def validate_local_repo(self):
        """Validates that the local repository path exists and is accessible."""
        if not self.local_repo_path or not self.local_repo_path.exists():
            raise RuntimeError('Local repository is not created or accessible.')
        validate_folder_access(self.local_repo_path)

    def commit_changes(
        self,
        commit_message: str = "Update",
        sync_to_origin: bool = False
    ) -> None:
        """
        Commits changes to the local repository and optionally pushes to remote.
        
        Args:
            commit_message: Message for the commit
            sync_to_origin: Whether to push changes to remote repository
        """
        self.validate_local_repo()
        repo = Repo(self.local_repo_path)
        repo.index.commit(commit_message)

        if sync_to_origin:
            origin = repo.remote(name="origin")
            origin.push()

    def get_template_info(self, template_id: str) -> TemplateItem:
        """
        Retrieves information for a specific template.
        
        Args:
            template_id: ID of the template to retrieve
            
        Returns:
            TemplateItem containing template information
            
        Raises:
            FileNotFoundError: If template info file is not found
        """
        self.validate_local_repo()
        template_dir = self.local_repo_path / template_id
        info_file_path = template_dir / FileNames.SOURCE_DIR / FileNames.INFO_YAML
        
        if not info_file_path.exists():
            raise FileNotFoundError(f'Template info file not found at: {info_file_path}')

        template_info = read_model(info_file_path, root_locator, TemplateInfo)
        return TemplateItem(id=template_dir.name, info=template_info)

    def get_templates_list(self) -> TemplatesList:
        """
        Returns a list of all available templates in the repository.
        
        Returns:
            List of TemplateItems
        """
        self.validate_local_repo()
        templates = []

        for template_dir in self.local_repo_path.iterdir():
            if template_dir.is_dir():
                info_file_path = template_dir / FileNames.SOURCE_DIR / FileNames.INFO_YAML
                if info_file_path.exists():
                    try:
                        template_info = read_model(info_file_path, root_locator, TemplateInfo)
                        templates.append(TemplateItem(id=template_dir.name, info=template_info))
                    except Exception:
                        continue
        return TemplatesList(root=templates)

    def get_template_directory(self, template_id: str) -> Path:
        """
        Gets the directory path for a specific template.
        
        Args:
            template_id: ID of the template
            
        Returns:
            Path to the template directory
            
        Raises:
            RuntimeError: If template directory is not accessible
        """
        template_dir = self.local_repo_path / template_id
        validate_folder_access(template_dir)
        return template_dir

    def upload_template(
        self,
        template_archive: UploadFile,
        commit_message: Optional[str] = None,
        sync_to_origin: bool = False
    ) -> str:
        """
        Uploads and extracts a template zip file to the repository.
        
        Args:
            template_archive: Uploaded zip file containing the template
            commit_message: Optional commit message
            sync_to_origin: Whether to push changes to remote
            
        Returns:
            ID of the newly created template
            
        Raises:
            RuntimeError: If repository is not accessible
        """
        self.validate_local_repo()
        base_name = Path(template_archive.filename).stem
        template_id = base_name
        
        # Generate unique name if folder exists
        target_dir = self.local_repo_path / template_id
        if target_dir.exists():
            timestamp = int(time.time())
            unique_suffix = uuid.uuid4().hex[:8]
            template_id = f"{base_name}_{timestamp}_{unique_suffix}"
            target_dir = self.local_repo_path / template_id

        target_dir.mkdir(parents=True, exist_ok=False)
        template_archive.file.seek(0)
        
        with zipfile.ZipFile(BytesIO(template_archive.file.read())) as zip_ref:
            zip_ref.extractall(target_dir)

        commit_msg = commit_message or f"Add template: {template_id}"
        repo = Repo(self.local_repo_path)
        repo.git.add(target_dir)
        self.commit_changes(commit_msg, sync_to_origin)
        return template_id

    def download_template(self, template_id: str) -> StreamingResponse:
        """
        Creates a zip archive of the template directory for download.
        
        Args:
            template_id: ID of the template to download
            
        Returns:
            StreamingResponse containing the zip file
            
        Raises:
            RuntimeError: If repository is not accessible
        """
        template_dir = self.get_template_directory(template_id)
        zip_buffer = BytesIO()

        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(template_dir):
                for file in files:
                    file_path = Path(root) / file
                    arcname = file_path.relative_to(template_dir)
                    zipf.write(file_path, arcname)

        zip_buffer.seek(0)
        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={"Content-Disposition": f'attachment; filename="{template_id}.vis"'}
        )

    def duplicate_template(
        self,
        source_template_id: str,
        sync_to_origin: bool = False
    ) -> str:
        """
        Creates a copy of an existing template with a unique name.
        
        Args:
            source_template_id: ID of the template to duplicate
            sync_to_origin: Whether to push changes to remote
            
        Returns:
            ID of the new template
            
        Raises:
            RuntimeError: If repository is not accessible
        """
        source_dir = self.get_template_directory(source_template_id)
        new_template_id = f"{source_template_id}_copy_{uuid.uuid4().hex[:8]}"
        target_dir = self.local_repo_path / new_template_id
        
        shutil.copytree(source_dir, target_dir)
        repo = Repo(self.local_repo_path)
        repo.git.add(target_dir)
        
        commit_msg = f"Duplicated template: {source_template_id} to {new_template_id}"
        self.commit_changes(commit_msg, sync_to_origin)
        return new_template_id

    def rename_template(
        self,
        current_template_id: str,
        new_template_id: str,
        sync_to_origin: bool = False
    ) -> str:
        """
        Renames a template directory.
        
        Args:
            current_template_id: Current ID of the template
            new_template_id: New ID for the template
            sync_to_origin: Whether to push changes to remote
            
        Returns:
            New template ID
            
        Raises:
            RuntimeError: If repository is not accessible
        """
        source_dir = self.local_repo_path / current_template_id
        target_dir = self.local_repo_path / new_template_id
        
        shutil.move(source_dir, target_dir)
        repo = Repo(self.local_repo_path)
        repo.git.add(target_dir)
        
        commit_msg = f"Renamed template: {current_template_id} to {new_template_id}"
        self.commit_changes(commit_msg, sync_to_origin)
        return new_template_id

    def delete_template(
        self,
        template_id: str,
        sync_to_origin: bool = False
    ) -> str:
        """
        Deletes a template from the repository.
        
        Args:
            template_id: ID of the template to delete
            sync_to_origin: Whether to push changes to remote
            
        Returns:
            ID of the deleted template
            
        Raises:
            RuntimeError: If repository is not accessible
        """
        template_dir = self.get_template_directory(template_id)
        shutil.rmtree(template_dir)

        repo = Repo(self.local_repo_path)
        deleted_files = [
            os.path.join(self.local_repo_path, f) 
            for f in repo.git.ls_files(template_dir).splitlines()
        ]

        if deleted_files:
            repo.index.remove(deleted_files, working_tree=True)

        commit_msg = f'Deleted template "{template_id}"'
        self.commit_changes(commit_msg, sync_to_origin)
        return template_id

    def get_template_variables(self, template_id: str) -> Variables:
        """
        Retrieves variables defined for a template.
        
        Args:
            template_id: ID of the template
            
        Returns:
            Variables object containing template variables
            
        Raises:
            RuntimeError: If variables file cannot be processed
        """
        template_dir = self.get_template_directory(template_id)
        variables_file = template_dir / FileNames.SOURCE_DIR / FileNames.VARIABLES_YAML
        
        if variables_file.exists():
            try:
                return read_model(variables_file, root_locator, Variables)
            except Exception:
                raise RuntimeError("Unable to process the variables file")
        return Variables(root=[])

    def upload_file_to_template(
        self,
        template_id: str,
        relative_path: List[str],
        file: UploadFile,
        commit_message: Optional[str] = None,
        sync_to_origin: bool = False
    ) -> Path:
        """
        Uploads a file to a template directory.
        
        Args:
            template_id: ID of the target template
            relative_path: Relative path within the template
            file: Uploaded file
            commit_message: Optional commit message
            sync_to_origin: Whether to push changes to remote
            
        Returns:
            Relative path to the uploaded file
            
        Raises:
            FileNotFoundError: If target directory doesn't exist
            RuntimeError: If repository is not accessible
        """
        template_dir = self.get_template_directory(template_id)
        target_dir = template_dir.joinpath(*relative_path)
    
        if not target_dir.exists():
            raise FileNotFoundError(f'Directory not found: {target_dir}')
        if not target_dir.is_dir():
            raise RuntimeError(f'Path is not a directory: {target_dir}')

        file.file.seek(0)
        target_file = target_dir / file.filename
        
        with open(target_file, "wb") as f:
            shutil.copyfileobj(file.file, f)

        commit_msg = commit_message or f"Added file: {target_file.relative_to(template_dir)}"
        repo = Repo(self.local_repo_path)
        repo.git.add(str(target_file))
        self.commit_changes(commit_msg, sync_to_origin)
    
        return target_file.relative_to(template_dir)

    def upload_folder_to_template(
        self,
        template_id: str,
        relative_path: List[str],
        folder_zip: UploadFile,
        commit_message: Optional[str] = None,
        sync_to_origin: bool = False
    ) -> Path:
        """
        Uploads and extracts a folder to a template directory.
        
        Args:
            template_id: ID of the target template
            relative_path: Relative path within the template
            folder_zip: Uploaded zip file containing folder contents
            commit_message: Optional commit message
            sync_to_origin: Whether to push changes to remote
            
        Returns:
            Relative path to the extracted folder
            
        Raises:
            FileNotFoundError: If target directory doesn't exist
            RuntimeError: If repository is not accessible
        """
        template_dir = self.get_template_directory(template_id)
        target_dir = template_dir.joinpath(*relative_path)

        if not target_dir.exists():
            raise FileNotFoundError(f'Directory not found: {target_dir}')
        if not target_dir.is_dir():
            raise RuntimeError(f'Path is not a directory: {target_dir}')

        folder_name = Path(folder_zip.filename).stem
        extraction_dir = target_dir / folder_name
        extraction_dir.mkdir(exist_ok=True)
    
        folder_zip.file.seek(0)
        with zipfile.ZipFile(BytesIO(folder_zip.file.read())) as zip_ref:
            zip_ref.extractall(extraction_dir)

        commit_msg = commit_message or f"Added folder: {extraction_dir.relative_to(template_dir)}"
        repo = Repo(self.local_repo_path)
        repo.git.add(str(extraction_dir))
        self.commit_changes(commit_msg, sync_to_origin)
    
        return extraction_dir.relative_to(template_dir)

    def delete_file_in_template(
        self,
        template_id: str,
        relative_path: List[str],
        sync_to_origin: bool = False
    ) -> Path:
        """
        Deletes a file or directory from a template.
        
        Args:
            template_id: ID of the target template
            relative_path: Relative path to the file/directory
            sync_to_origin: Whether to push changes to remote
            
        Returns:
            Relative path to the deleted file/directory
            
        Raises:
            FileNotFoundError: If target doesn't exist
            RuntimeError: If repository is not accessible
        """
        template_dir = self.get_template_directory(template_id)
        target_path = template_dir.joinpath(*relative_path)

        if not target_path.exists():
            raise FileNotFoundError(f'Path not found: {target_path}')

        repo = Repo(self.local_repo_path)
        if target_path.is_file():
            os.remove(target_path)
            deleted_files = [target_path.relative_to(self.local_repo_path)]
        elif target_path.is_dir():
            shutil.rmtree(target_path)
            deleted_files = repo.git.ls_files(target_path).splitlines()

        if deleted_files:
            repo.index.remove(deleted_files, working_tree=True)

        commit_msg = f'Deleted: {target_path.relative_to(template_dir)}'
        self.commit_changes(commit_msg, sync_to_origin)
        return target_path.relative_to(template_dir)

    def download_file_from_template(
        self,
        template_id: str,
        relative_path: List[str],
    ) -> Union[FileResponse, StreamingResponse]:
        """
        Downloads a file or directory from a template.
        
        Args:
            template_id: ID of the target template
            relative_path: Relative path to the file/directory
            
        Returns:
            FileResponse for single files, StreamingResponse (zip) for directories
            
        Raises:
            FileNotFoundError: If target doesn't exist
            RuntimeError: If repository is not accessible
        """
        template_dir = self.get_template_directory(template_id)
        target_path = template_dir.joinpath(*relative_path)

        if not target_path.exists():
            raise FileNotFoundError(f'Path not found: {target_path}')

        if target_path.is_file():
            return FileResponse(target_path, filename=target_path.name)
        
        # Handle directory case
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(target_path):
                for file in files:
                    file_path = Path(root) / file
                    arcname = file_path.relative_to(target_path)
                    zipf.write(file_path, arcname)

        zip_buffer.seek(0)
        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={"Content-Disposition": f'attachment; filename="{target_path.name}.zip"'}
        )

    def duplicate_file_in_template(
        self,
        template_id: str,
        relative_path: List[str],
        sync_to_origin: bool = False
    ) -> Path:
        """
        Creates a copy of a file/directory in the same location with a unique name.
        
        Args:
            template_id: ID of the target template
            relative_path: Relative path to the file/directory
            sync_to_origin: Whether to push changes to remote
            
        Returns:
            Relative path to the new copy
            
        Raises:
            FileNotFoundError: If source doesn't exist
            RuntimeError: If repository is not accessible
        """
        template_dir = self.get_template_directory(template_id)
        source_path = template_dir.joinpath(*relative_path)
    
        if not source_path.exists():
            raise FileNotFoundError(f'Path not found: {source_path}')

        unique_suffix = uuid.uuid4().hex[:8]
        if source_path.is_file():
            new_path = source_path.with_name(
                f"{source_path.stem}_copy_{unique_suffix}{source_path.suffix}"
            )
            shutil.copyfile(source_path, new_path)
        else:
            new_path = source_path.with_name(f"{source_path.name}_copy_{unique_suffix}")
            shutil.copytree(source_path, new_path)

        commit_msg = f"Duplicated: {source_path.relative_to(template_dir)} to {new_path.relative_to(template_dir)}"
        repo = Repo(self.local_repo_path)
        repo.git.add(str(new_path))
        self.commit_changes(commit_msg, sync_to_origin)
    
        return new_path.relative_to(template_dir)

    def rename_file_in_template(
        self,
        template_id: str,
        relative_path: List[str],
        new_name: str,
        sync_to_origin: bool = False
    ) -> Path:
        """
        Renames a file/directory within a template.
        
        Args:
            template_id: ID of the target template
            relative_path: Relative path to the file/directory
            new_name: New name for the file/directory
            sync_to_origin: Whether to push changes to remote
            
        Returns:
            Relative path to the renamed file/directory
            
        Raises:
            FileNotFoundError: If source doesn't exist
            RuntimeError: If repository is not accessible
        """
        template_dir = self.get_template_directory(template_id)
        source_path = template_dir.joinpath(*relative_path)
    
        if not source_path.exists():
            raise FileNotFoundError(f'Path not found: {source_path}')

        new_path = source_path.parent / new_name
        shutil.move(source_path, new_path)

        commit_msg = f"Renamed: {source_path.relative_to(template_dir)} to {new_path.relative_to(template_dir)}"
        repo = Repo(self.local_repo_path)
        repo.git.add(str(new_path))
        self.commit_changes(commit_msg, sync_to_origin)
    
        return new_path.relative_to(template_dir)

    def get_template_file_tree(
        self,
        template_id: str,
        relative_path: List[str],
    ) -> PathTree:
        """
        Gets the directory tree structure for a template path.
        
        Args:
            template_id: ID of the target template
            relative_path: Relative path within the template
            
        Returns:
            PathTree object representing the directory structure
            
        Raises:
            FileNotFoundError: If path doesn't exist
            RuntimeError: If path is not a directory
        """
        template_dir = self.get_template_directory(template_id)
        dir_path = template_dir.joinpath(*relative_path)

        if not dir_path.exists():
            raise FileNotFoundError(f'Directory not found: {dir_path}')
        if not dir_path.is_dir():
            raise RuntimeError(f'Path is not a directory: {dir_path}')

        return get_path_tree(dir_path, base_path=template_dir, as_posix=True, skip_root=True)
