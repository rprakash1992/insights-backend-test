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

DEFAULT_TEMPLATES_DIR_NAME = None
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
    def __init__(self,
                 repo_url: Optional[str] = None,
                 env_var: Optional[str] = EnvVar.DEFAULT_REPO,
                 default_parent_dir: Optional[Union[str, Path]] = None,
                 templates_dir_name: Optional[Union[str, Path]] = DEFAULT_TEMPLATES_DIR_NAME,
                 ):
        """Initializes the TemplateRepositoryManager."""
        if repo_url is not None:
            self.repo_url = repo_url
        elif env_var:
            self.repo_url = os.getenv(env_var)
        else:
            self.repo_url = None
        self.default_parent_dir = Path(default_parent_dir).expanduser() if default_parent_dir else Path.cwd()
        self.templates_dir_name = templates_dir_name
        self.templates_dir_path = None

    def create_directory(self) -> Path:
        """
        Clones the repository to the specified parent directory.
        """
        if not self.repo_url:
            raise ValueError("Repository URL is not specified.")

        target_dir = self.default_parent_dir / (self.templates_dir_name or Path(self.repo_url).stem)
        if target_dir.exists():
            raise FileExistsError(f"Target directory {target_dir} already exists.")

        try:
            Repo.clone_from(self.repo_url, target_dir)
            self.templates_dir_path = Path(target_dir)
            return self.templates_dir_path
        except git.exc.GitCommandError as e:
            raise RuntimeError(f"Failed to clone repository: {e}")

    def validate_templates_dir_path(self):
        if self.templates_dir_path is None:
            raise RuntimeError('Templates directory is not created.')

        validate_folder_access(self.templates_dir_path)

    def commit_changes(self,
                        commit_message: Optional[str] = None,
                        sync_to_origin: Optional[bool] = None) -> None:
        self.validate_templates_dir_path()

        if not commit_message:
            commit_message = f"Update"

        repo = Repo(self.templates_dir_path)
        repo.index.commit(commit_message)

        if sync_to_origin:
            origin = repo.remote(name="origin")
            origin.push()


    def template_info(self, template_name) -> TemplateItem:
        self.validate_templates_dir_path()

        template_dir = Path(self.templates_dir_path / template_name).resolve()
        info_yaml_path = template_dir / FileNames.SOURCE_DIR / FileNames.INFO_YAML
        if not info_yaml_path.exists():
            raise FileNotFoundError(f'Template information file \"info_yaml_path\" not found.')

        template_info = read_model(info_yaml_path, root_locator, TemplateInfo)
        return TemplateItem(
            id=template_dir.name,
            info=template_info
        )

    def get_templates_list(self) -> TemplatesList:
        """
        Returns a list of templates available in the cloned repository.
        This method parses the repository and returns template information.
        """
        self.validate_templates_dir_path()

        templates = []

        for template_dir in self.templates_dir_path.iterdir():
            if template_dir.is_dir():
                info_yaml_path = template_dir / FileNames.SOURCE_DIR / FileNames.INFO_YAML
                if info_yaml_path.exists():
                    try:
                        template_info = read_model(info_yaml_path, root_locator, TemplateInfo)
                        templates.append(TemplateItem(
                            id=template_dir.name,  # Fixed: use .name instead of .filename
                            info=template_info))
                    except Exception:
                        # Optionally log or handle errors for individual templates
                        continue
        return TemplatesList(root=templates)

    def template_directory(self, template_name) -> Path:
        template_dir = Path(self.templates_dir_path / template_name).resolve()
        validate_folder_access(template_dir)
        return template_dir

    def upload_template(self, new_template: UploadFile,
                        commit_message: Optional[str] = None,
                        sync_to_origin: bool = False) -> str:
        """
        Uploads a template zip file and extracts it to the repository.
        If a folder with the same name exists, a unique name is generated.
        Args:
            new_template: FastAPI UploadFile object representing the uploaded zip file.
        Returns:
            The template ID (folder name) where the template was extracted.
        """
        # Get the template name from the uploaded file (without extension)
        template_name = Path(new_template.filename).stem
        target_dir = self.templates_dir_path / template_name

        # If the folder exists, create a unique name
        if target_dir.exists():
            timestamp = int(time.time())
            unique_name = uuid.uuid4().hex[:8]
            template_name = f"template_{timestamp}_{unique_name}"
            target_dir = self.templates_dir_path / template_name

        # Create the target directory
        target_dir.mkdir(parents=True, exist_ok=False)

        # Extract the zip file contents to the target directory
        # Use new_template.file.read() for UploadFile, but ensure the file pointer is at the start
        new_template.file.seek(0)
        with zipfile.ZipFile(BytesIO(new_template.file.read())) as zip_ref:
            zip_ref.extractall(target_dir)

        if not commit_message:
            commit_message = f"Add template: {template_name}"

        # Commit and push the new template to the remote repository
        repo = Repo(self.templates_dir_path)
        repo.git.add(target_dir)
        self.commit_changes(commit_message, sync_to_origin)
        return template_name

    def download_template(self, template_name: str) -> StreamingResponse:
        """
        Creates a zip archive of the template directory and returns it as a StreamingResponse.
        The root of the zip will contain the template contents directly, not the template folder.
        """
        template_dir = self.template_directory(template_name)
        zip_buffer = BytesIO()

        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(template_dir):
                for file in files:
                    file_path = Path(root) / file
                    arcname = file_path.relative_to(template_dir)
                    zipf.write(file_path, arcname)

        zip_buffer.seek(0)
        filename = f"{template_name}.vis"
        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )

    def duplicate_template(self, source_template_name: str,
                        sync_to_origin: bool = False) -> str:
        """
        Makes a copy of an existing template.  A unique name is generated for the
        newly created template.

        Args:
            template_name: Template that needs to be duplicated.
        Returns:
            The template ID (folder name) of the newly created template.
        """
        source_dir = self.templates_dir_path / source_template_name
        validate_folder_access(source_dir)
        unique_id = uuid.uuid4().hex[:8]
        dest_template_name = f"{source_template_name}_copy_{unique_id}"
        target_dir = self.templates_dir_path / dest_template_name
        shutil.copytree(source_dir, target_dir)

        commit_message = f"Created a duplicate of template: {source_template_name} at {dest_template_name}"

        # Commit and push the new template to the remote repository
        repo = Repo(self.templates_dir_path)
        repo.git.add(target_dir)
        self.commit_changes(commit_message, sync_to_origin)
        return dest_template_name

    def rename_template(self, source_template_name: str,
                        dest_template_name: str,
                        sync_to_origin: bool = False) -> str:
        """
        Renames a template.

        Args:
            template_name: Template that needs to be duplicated.
        Returns:
            The template ID (folder name) of the newly created template.
        """
        source_dir = self.templates_dir_path / source_template_name
        target_dir = self.templates_dir_path / dest_template_name
        #new_target_path = "/".join(relative_path[:-1] + [new_name])
        shutil.move(source_dir, target_dir)

        commit_message = f"Rename template: {source_template_name} -> {dest_template_name}"

        # Commit and push the new template to the remote repository
        repo = Repo(self.templates_dir_path)
        # Stage the changes (Git detects renames automatically)
        repo.git.add(target_dir)
        self.commit_changes(commit_message, sync_to_origin)

        return dest_template_name

    def delete_template(self, template_name: str,
                        sync_to_origin: bool = False) -> str:
        """
        Deletes a template.

        Args:
            template_name: Template that needs to be duplicated.
        Returns:
            The template ID (folder name) of the deleted template.
        """
        template_dir = self.template_directory(template_name)
        if os.path.exists(template_dir):
            shutil.rmtree(template_dir)

        repo = Repo(self.templates_dir_path)
        deleted_files = [
            os.path.join(self.templates_dir_path, f) 
            for f in repo.git.ls_files(template_dir).splitlines()
        ]

        if deleted_files:
            repo.index.remove(deleted_files, working_tree=True)

        commit_message = f'Deleted template "{template_name}"'
        self.commit_changes(commit_message, sync_to_origin)

        return template_name

    def template_variables(self,  template_name: str) ->  Variables:
        template_dir = self.template_directory(template_name)
        variables_yaml_path = template_dir / FileNames.SOURCE_DIR / FileNames.VARIABLES_YAML
        if variables_yaml_path.exists():
            try:
                variables = read_model(variables_yaml_path, root_locator, Variables)
                return variables
            except Exception:
                raise RuntimeError("Unable to process the variables.yaml file")
        else:
            return Variables(root=[])

    def upload_file(
        self,
        template_name: str,
        path_components: List[str],
        new_file: UploadFile,
        commit_message: Optional[str] = None,
        sync_to_origin: bool = False
    ) -> str:
        """Upload a single file to the template repository"""
        template_dir = self.template_directory(template_name)
        target_dir = Path(template_dir).joinpath(*path_components)
    
        # Validate target directory
        if not target_dir.exists():
            raise FileNotFoundError(f'Path not found: "{target_dir}"')
        if not target_dir.is_dir():
            raise RuntimeError(f'Path "{target_dir}" is not a directory')

        # Reset file pointer
        new_file.file.seek(0)

        # Save file
        target_file_path = target_dir / new_file.filename
        with open(target_file_path, "wb") as temp_file:
            shutil.copyfileobj(new_file.file, temp_file)

        # Commit changes
        if not commit_message:
            commit_message = f"Add file: {target_file_path.relative_to(template_dir)}"

        repo = Repo(self.templates_dir_path)
        repo.git.add(str(target_file_path))
        self.commit_changes(commit_message, sync_to_origin)
    
        return target_file_path.relative_to(template_dir.parent)

    def upload_folder(
        self,
        template_name: str,
        path_components: List[str],
        folder_archive: UploadFile,
        commit_message: Optional[str] = None,
        sync_to_origin: bool = False
    ) -> str:
        """Upload and extract a folder archive to the template repository"""
        template_dir = self.template_directory(template_name)
        target_dir = Path(template_dir).joinpath(*path_components)

        # Validate target directory
        if not target_dir.exists():
            raise FileNotFoundError(f'Path not found: "{target_dir}"')
        if not target_dir.is_dir():
            raise RuntimeError(f'Path "{target_dir}" is not a directory')

        # Reset file pointer
        folder_archive.file.seek(0)

        # Create subdirectory named after the archive (without extension)
        archive_name = Path(folder_archive.filename).stem
        extraction_dir = target_dir / archive_name
        extraction_dir.mkdir(exist_ok=True)
    
        # Extract archive contents
        with zipfile.ZipFile(BytesIO(folder_archive.file.read())) as zip_ref:
            zip_ref.extractall(extraction_dir)

        # Commit changes
        if not commit_message:
            commit_message = f"Add folder: {extraction_dir.relative_to(template_dir)}"

        repo = Repo(self.templates_dir_path)
        repo.git.add(str(extraction_dir))
        self.commit_changes(commit_message, sync_to_origin)
    
        return extraction_dir.relative_to(template_dir.parent)

    def delete_file(
        self,
        template_name: str,
        path_components: List[str],
        commit_message: Optional[str] = None,
        sync_to_origin: bool = False
    ) -> str:
        """Upload and extract a folder archive to the template repository"""
        template_dir = self.template_directory(template_name)
        target_file = Path(template_dir).joinpath(*path_components)

        # Validate target file
        if not target_file.exists():
            raise FileNotFoundError(f'Path not found: "{target_file}"')

        repo = Repo(self.templates_dir_path)
        if target_file.is_file():
            os.remove(target_file)
            deleted_files = [target_file.relative_to(self.templates_dir_path)]

        elif target_file.is_dir():
            shutil.rmtree(target_file)
            deleted_files = repo.git.ls_files(target_file).splitlines()

        if deleted_files:
            repo.index.remove(deleted_files, working_tree=True)

        commit_message = f'Deleted file/directory "{target_file}"'
        self.commit_changes(commit_message, sync_to_origin)

        return target_file

    def download_file(
        self,
        template_name: str,
        path_components: List[str],
    ) -> Union[FileResponse, StreamingResponse]:
        """
        Creates a zip archive of the template directory and returns it as a StreamingResponse.
        The root of the zip will contain the template contents directly, not the template folder.
        """
        template_dir = self.template_directory(template_name)
        target_file = Path(template_dir).joinpath(*path_components)

        if not target_file.exists():
            raise FileNotFoundError(f'Path not found: "{target_file}"')

        if target_file.is_file():
            return FileResponse(target_file, filename=target_file.name)
        elif target_file.is_dir():
            zip_buffer = BytesIO()

            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
                for root, _, files in os.walk(target_file):
                    for file in files:
                        file_path = Path(root) / file
                        arcname = file_path.relative_to(target_file)
                        zipf.write(file_path, arcname)

            zip_buffer.seek(0)
            filename = f"{target_file.name}.zip"
            return StreamingResponse(
                zip_buffer,
                media_type="application/zip",
                headers={"Content-Disposition": f'attachment; filename="{filename}"'}
            )

    def duplicate_file(
        self,
        template_name: str,
        path_components: List[str],
        commit_message: Optional[str] = None,
        sync_to_origin: bool = False
    ) -> str:
        """Duplicate a file in the template repository"""
        template_dir = self.template_directory(template_name)
        source_file_path = Path(template_dir).joinpath(*path_components)
    
        if not source_file_path.exists():
            raise FileNotFoundError(f'Path not found: "{source_file_path}"')

        unique_id = uuid.uuid4().hex[:8]
        dest_file_path = source_file_path.with_name(f"{source_file_path.stem}_copy_{unique_id}{source_file_path.suffix}")
        if source_file_path.is_file():
            shutil.copyfile(source_file_path, dest_file_path)
        elif source_file_path.is_dir():
            shutil.copytree(source_file_path, dest_file_path)

        # Commit changes
        if not commit_message:
            commit_message = f"Duplicated file: {source_file_path.relative_to(template_dir)} to {dest_file_path.relative_to(template_dir)}"

        repo = Repo(self.templates_dir_path)
        repo.git.add(str(dest_file_path))
        self.commit_changes(commit_message, sync_to_origin)
    
        return dest_file_path.relative_to(template_dir.parent)

    def rename_file(
        self,
        template_name: str,
        path_components: List[str],
        new_name: str,
        commit_message: Optional[str] = None,
        sync_to_origin: bool = False
    ) -> str:
        """Rename a file in the template repository"""
        template_dir = self.template_directory(template_name)
        source_file_path = Path(template_dir).joinpath(*path_components)
    
        if not source_file_path.exists():
            raise FileNotFoundError(f'Path not found: "{source_file_path}"')

        dest_file_path = source_file_path.parent / new_name
        shutil.move(source_file_path, dest_file_path)

        # Commit changes
        if not commit_message:
            commit_message = (
                f"Renamed file: {source_file_path.relative_to(template_dir)} "
                f"to {dest_file_path.relative_to(template_dir)}"
            )

        repo = Repo(self.templates_dir_path)
        repo.git.add(str(dest_file_path))
        self.commit_changes(commit_message, sync_to_origin)
    
        return dest_file_path.relative_to(template_dir.parent)


    def file_tree(
        self,
        template_name: str,
        path_components: List[str],
    ) -> PathTree:
        template_dir = self.template_directory(template_name)
        file_path = Path(template_dir.joinpath(*path_components))

        if not file_path.exists():
            raise FileNotFoundError(f'File not found: \"file_path\"')

        if not file_path.is_dir():
            raise RuntimeError(f'Path "{file_path}" is not a directory')

        return get_path_tree(file_path, base_path=template_dir,
                             as_posix=True, skip_root=True)
