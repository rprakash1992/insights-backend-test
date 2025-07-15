#!/usr/bin/env python

# Copyright (C) 2018 Visual Collaboration Technologies Inc.
# All Rights Reserved.
#
# This file is a property of Visual Collaboration Technologies Inc.
# Unauthorized access, reproduction or redistribution of any kind is prohibited.
"""
TemplateFileManager class provides methods to manage files in a template directory.
"""

from pathlib import Path
from typing import List, Union
from fastapi import UploadFile
from starlette.responses import FileResponse, StreamingResponse
import shutil
import uuid
from typing import Optional

from vcti.util.path_tree import PathTree, get_path_tree
from vcti.util.path_utils import validate_folder_access
from vcti.archive.directory_zip_memory_streamer import DirectoryZipMemoryStreamer
from vcti.archive.zip_extractor import ZipExtractor


class TemplateFileManager:
    def __init__(self, template_path: Path, repo_root: Path):
        """
        Handles all file operations for a template.
        
        Args:
            template_path: Absolute path to template directory
            repo_root: Absolute path to repository root
        """
        self.path = template_path.resolve()
        self.repo_root = repo_root.resolve()
        self._validate_paths()

    def _validate_paths(self):
        """Validate during init that template_path is within repo_root"""
        try:
            self.path.relative_to(self.repo_root)
        except ValueError:
            raise ValueError(
                f"Template path {self.path} must be within {self.repo_root}"
            )
        # Ensure  that template_path exists and accessible
        validate_folder_access(self.path)

    def _validate_relative_path(self, relative_path: List[str]):
        """
        Pure validation method - raises exceptions only
        Checks for:
        1. Invalid path components (., .., etc.)
        2. Path traversal attempts
        3. Empty components
        """
        if not isinstance(relative_path, list):
            raise TypeError("Path must be a list of components")
            
        forbidden = {'', '.', '..'}
        for part in relative_path:
            if part in forbidden:
                raise ValueError(f"Forbidden path component: '{part}'")
            if '/' in part or '\\' in part:
                raise ValueError("Path components cannot contain separators")

        # Verify the full path stays within repo
        try:
            full_path = self.path.joinpath(*relative_path).resolve()
            full_path.relative_to(self.repo_root)
        except (ValueError, RuntimeError) as e:
            raise ValueError(
                f"Path escapes template directory: {relative_path}"
            ) from e

    def get_file_tree(self, relative_path: List[str] = []) -> PathTree:
        """Returns directory structure for template path"""
        base_path = self.path.joinpath(*relative_path) if relative_path else self.path
        return get_path_tree(base_path, base_path=self.path.parent, as_posix=True, skip_root=True)

    def download_directory(
            self,
            relative_path: List[str] = [],
            file_name: Optional[str] = None,
    ) -> StreamingResponse:
        """
        Downloads a directory from the template into an archive.
    
        Returns:
            StreamingResponse: Configured zip stream response

        Note:
            Suitable for smaller templates where memory usage isn't a concern.
            For large templates (>100MB), prefer the tempfile version.
        """
        target_path = self.path.joinpath(*relative_path)

        if not target_path.exists():
            raise FileNotFoundError(f"Path not found: {target_path}")
        if not target_path.is_dir():
            raise NotADirectoryError(f"Path is not a directory: {target_path}")

        if file_name is None:
            file_name = f"{target_path.name}.zip"

        return StreamingResponse(
            content=DirectoryZipMemoryStreamer(target_path),
            media_type="application/zip",
            headers={
                "Content-Disposition": f'attachment; filename="{file_name}"'
            }
        )

    def download_file(
            self,
            relative_path: List[str] = [],
            file_name: Optional[str] =  None,
    ) -> FileResponse:
        """Downloads a file from template"""
        target_path = self.path.joinpath(*relative_path)

        if not target_path.exists():
            raise FileNotFoundError(f"Path not found: {target_path}")
        if not target_path.is_file():
            raise IsADirectoryError(f"Path is a directory and not a file: {target_path}")

        if file_name is None:
            file_name = target_path.name

        return FileResponse(target_path, filename=file_name)

    def download_file_or_directory(
            self,
            relative_path: List[str] = [],
            file_name: Optional[str] = None,
    ) -> Union[FileResponse, StreamingResponse]:
        """Downloads a file or directory from template"""
        target_path = self.path.joinpath(*relative_path)
        if not target_path.exists():
            raise FileNotFoundError(f"Path not found: {target_path}")

        if target_path.is_file():
            return self.download_file(relative_path, file_name)
        elif target_path.is_dir():
            return self.download_directory(relative_path, file_name)
        else:
            raise RuntimeError(f'Runtime Error: Unable to access "{target_path}"')

    def rename(self, source_relative_path: List[str], new_name: str) -> Path:
        """Renames a file/directory"""
        source_path = self.path.joinpath(*source_relative_path)
        if not source_path.exists():
            raise FileNotFoundError(f"File/directory not found: {source_path}")

        dest_name = new_name
        dest_path = source_path.with_name(dest_name)
        shutil.move(source_path, dest_path)
        return dest_path.relative_to(self.path.parent)

    def duplicate(self, source_relative_path: List[str]) -> Path:
        """Creates a copy of a file with unique suffix"""
        source_path = self.path.joinpath(*source_relative_path)
        if not source_path.exists():
            raise FileNotFoundError(f"File/directory not found: {source_path}")
        dest_name = f"{source_path.stem}_copy_{uuid.uuid4().hex[:8]}{source_path.suffix}"
        dest_path = source_path.with_name(dest_name)
        if source_path.is_file():
            shutil.copy2(source_path, dest_path)
        elif source_path.is_dir():
            shutil.copytree(source_path, dest_path)
        return dest_path.relative_to(self.path.parent)

    def upload_file_or_directory(self, relative_path: List[str], file: UploadFile, is_directory: bool) -> Path:
        """
        Uploads a file/directory to the template.

        Args:
            relative_path: Path components to the target file/directory location (relative to template root).
            file: The UploadFile object.

        Returns:
            Path relative to template base path of the uploaded file/directory.

        Raises:
            FileNotFoundError: If parent directory doesn't exist.
            FileExistsError: If file/directory already exists.
            RuntimeError: On upload failure.
        """
        self._validate_relative_path(relative_path)
        target_file_or_dir = self.path.joinpath(*relative_path)
        parent_dir = target_file_or_dir.parent
        if not parent_dir.exists():
            raise FileNotFoundError(f"Directory not found: {parent_dir}")
        if target_file_or_dir.exists():
            raise FileExistsError('Target "%s" already exists', target_file_or_dir)

        file.file.seek(0)
        try:
            try:
                file.file.seek(0)
            except Exception:
                pass  # Some file-like objects may not support seek

            if is_directory:
                zip_extractor = ZipExtractor(file, target_file_or_dir)
                zip_extractor.extract_using_bytesio()
            else:
                with open(target_file_or_dir, "wb") as f:
                    shutil.copyfileobj(file.file, f)
        except Exception as e:
            if target_file_or_dir.exists():
                try:
                    if is_directory:
                        shutil.rmtree(target_file_or_dir)
                    else:
                        target_file_or_dir.unlink()  # Clean up partial upload
                except Exception:
                    pass
            raise RuntimeError(f"Upload failed: {str(e)}")

        return target_file_or_dir.relative_to(self.path.parent)

    def delete(self, relative_path: List[str]) -> Path:
        """Deletes a file/directory associated with the template """
        target_path = self.path.joinpath(*relative_path)
        if not target_path.exists():
            raise FileNotFoundError(f"Path not found: {target_path}")

        if target_path.is_file():
           target_path.unlink()
        elif target_path.is_dir():
            shutil.rmtree(target_path)
        else:
            raise RuntimeError(f'Runtime Error: Unable to access "{target_path}"')
        return target_path.relative_to(self.path.parent)