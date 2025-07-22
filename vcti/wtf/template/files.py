#!/usr/bin/env python

# Copyright (C) 2018 Visual Collaboration Technologies Inc.
# All Rights Reserved.
#
# This file is the property of Visual Collaboration Technologies Inc.
# Unauthorized access, reproduction, or redistribution of any kind is prohibited.
"""
TemplateFiles class provides methods to manage files in a template directory.
"""

import shutil
from pathlib import Path
from typing import Optional, Union

from fastapi import UploadFile
from starlette.responses import FileResponse, StreamingResponse

from vcti.archive.directory_zip_memory_streamer import DirectoryZipMemoryStreamer
from vcti.archive.zip_extractor import ZipExtractor
from vcti.util.file_id_utils import FileId
from vcti.util.path_tree import PathTree, get_path_tree
from vcti.util.path_utils import FileNameValidator, validate_folder_access

from .utils import make_duplicate_name


class TemplateFiles:
    def __init__(self, template_path: Path):
        """
        Handles all file operations for a template.

        Args:
            template_path: Absolute path to template directory
        """
        self.path = template_path.resolve()

        # Ensure that template_path exists and accessible
        validate_folder_access(self.path)

    def resolve_path(
        self,
        file_id: Optional[str] = None,
        *,
        must_exist: Optional[bool] = None,
        must_be_dir: Optional[bool] = None,
        must_be_file: Optional[bool] = None,
    ) -> Path:
        """
        Resolve the path of a file or directory associated with the template given its identifier.

        The file_id must be a POSIX-style file identifier.

        Example: A `file_id` of `abc/xyz` means that:
        - If the template root is `/path/to/template` (on Linux/Unix/Mac),
          then we are referring to the file/directory at `/path/to/template/abc/xyz`.
        - If the template root is `D:\\path\\to\\template` (on Microsoft Windows),
          then we are referring to the file/directory at `D:\\path\\to\\template\\abc\\xyz`.

        If no identifier is provided, returns the root of the template itself.

        Args:
            file_id (Optional[str]): POSIX-style relative path under template root.
            must_exist (Optional[bool]): Raise FileNotFoundError if path doesn't exist.
            must_be_dir (Optional[bool]): Raise NotADirectoryError if not a dir.
            must_be_file (Optional[bool]): Raise IsADirectoryError if not a file.

        Returns:
            Path: Resolved absolute path.

        Raises:
            ValueError: If file_id is invalid or attempts to escape root.
            FileNotFoundError, NotADirectoryError, IsADirectoryError: As per flags.
        """
        return FileId.resolve_path(
            file_id,
            self.path,
            must_exist=must_exist,
            must_be_dir=must_be_dir,
            must_be_file=must_be_file,
        )

    def get_file_id(self, file_path: Path) -> str:
        """
        Returns the file identifier for a file or directory within the template.
        The identifier is computed as the POSIX-style relative path of the file
        with respect to the template root directory.

        If the path refers to a directory (and is not the template root itself),
        the returned identifier ends with a forward slash.

        Args:
            file_path (Path): The absolute path to a file or directory within the template.

        Returns:
            str: The POSIX-style relative file identifier.

        Raises:
            ValueError: If the given path is not under the template root.
        """
        return FileId.get_file_id(
            file_path,
            self.path,
        )

    def get_directory_tree(
        self,
        file_id: Optional[str] = None,
    ) -> PathTree:
        """
        Return the hierarchical structure of a directory within the template.

        This method inspects the directory specified by `file_id` and returns
        a tree-like structure representing its contents (excluding the root directory itself).

        Args:
            file_id (Optional[str]):
                POSIX-style relative identifier for a directory under the template root.

        Returns:
            PathTree: Hierarchical structure of files and directories under the given path.

        Raises:
            FileNotFoundError: If the resolved path does not exist.
            NotADirectoryError: If the resolved path is not a directory.
        """
        file_path = self.resolve_path(file_id, must_be_dir=True)

        return get_path_tree(
            file_path,
            base_path=self.path.parent,
            as_posix=True,
            skip_root=True,
        )

    def download_directory(
        self,
        file_id: Optional[str] = None,
        download_filename: Optional[str] = None,
    ) -> StreamingResponse:
        """
        Create a downloadable ZIP archive of a directory within the template.

        Args:
            file_id (Optional[str]): File identifier (POSIX-style relative path)
                of the directory to archive. If None, the template root directory is used.
            download_filename (Optional[str]): Name of the resulting archive file.
                Defaults to "<directory_name>.zip" if not specified.

        Returns:
            StreamingResponse: A streaming HTTP response that downloads the ZIP archive.

        Raises:
            FileNotFoundError: If the resolved directory does not exist.
            NotADirectoryError: If the resolved path is not a directory.
        """
        dir_path = self.resolve_path(file_id, must_be_dir=True)

        if download_filename is None:
            download_filename = f"{dir_path.name}.zip"

        return StreamingResponse(
            content=DirectoryZipMemoryStreamer(dir_path),
            media_type="application/zip",
            headers={
                "Content-Disposition": f'attachment; filename="{download_filename}"'
            },
        )

    def download_file(
        self,
        file_id: Optional[str] = None,
        download_filename: Optional[str] = None,
    ) -> FileResponse:
        """
        Download a single file from the template.

        Args:
            file_id (Optional[str]): POSIX-style identifier of the file relative to the template root.
                                     If None, the template root is used.
            download_filename (Optional[str]): Optional filename to use for the downloaded file.
                                               Defaults to the actual file name.

        Returns:
            FileResponse: A response that initiates file download.

        Raises:
            FileNotFoundError: If the file does not exist.
            IsADirectoryError: If the resolved path is a directory instead of a file.
        """
        file_path = self.resolve_path(file_id, must_be_file=True)

        if download_filename is None:
            download_filename = file_path.name

        return FileResponse(file_path, filename=download_filename)

    def download(
        self,
        file_id: Optional[str] = None,
        download_filename: Optional[str] = None,
    ) -> Union[FileResponse, StreamingResponse]:
        """
        Download either a file or a directory from the template.

        Args:
            file_id (Optional[str]): POSIX-style identifier of the file or directory relative to the template root.
                                     If None, the template root is used.
            download_filename (Optional[str]): Optional filename to use for the download.
                                               For directories, a `.zip` extension is automatically added if omitted.

        Returns:
            Union[FileResponse, StreamingResponse]: A response that initiates download.
                - FileResponse for files
                - StreamingResponse for directories

        Raises:
            FileNotFoundError: If the specified path does not exist.
            RuntimeError: If the path exists but is neither a file nor a directory.
        """
        file_path = self.resolve_path(file_id, must_exist=True)

        if file_path.is_file():
            return self.download_file(file_id, download_filename)
        elif file_path.is_dir():
            return self.download_directory(file_id, download_filename)
        else:
            raise RuntimeError(
                f'Unexpected path type: "{file_path}" is neither a file nor a directory.'
            )

    def rename(
        self,
        file_id: str,
        new_name: str,
    ) -> str:
        """
        Rename a file or directory within the template.

        Args:
            file_id (str): Identifier (POSIX-style path) of the item to rename.
            new_name (str): New name (not path) to assign to the item.

        Returns:
            str: New file identifier (relative POSIX-style path).

        Raises:
            ValueError: If `new_name` is invalid or already exists.
        """
        FileNameValidator.validate(new_name)

        original_path = self.resolve_path(file_id, must_exist=True)

        new_path = original_path.with_name(new_name)
        if new_path.exists():
            raise FileExistsError(f"Target name already exists: {new_path}")

        shutil.move(original_path, new_path)
        return self.get_file_id(new_path)

    def duplicate(
        self,
        file_id: str,
    ) -> str:
        """
        Duplicate a file or directory, appending a unique suffix to avoid name clashes.

        Args:
            file_id (str): Identifier (POSIX-style path) of the item to duplicate.

        Returns:
            str: File identifier of the duplicated item.
        """
        source_path = self.resolve_path(file_id, must_exist=True)
        new_name = make_duplicate_name(source_path)
        dest_path = source_path.with_name(new_name)

        if source_path.is_file():
            shutil.copy2(source_path, dest_path)
        elif source_path.is_dir():
            shutil.copytree(source_path, dest_path)
        else:
            raise RuntimeError(f"Cannot duplicate path: {source_path}")

        return self.get_file_id(dest_path)

    def upload(
        self,
        file_id: str,
        file: UploadFile,
        is_directory: bool = False,
        create_parents: bool = False,
        replace_existing: bool = False,
    ) -> str:
        """
        Upload a file or a zipped directory to a location inside the template directory.

        Args:
            file_id (str): File identifier relative to the template root (in POSIX format).
            file (UploadFile): The uploaded file object.
            is_directory (bool): If True, treat the file as a zipped directory and extract it.
            create_parents (bool): If True, create parent directories if they don’t exist.
            replace_existing (bool): If True, overwrite existing files or directories.

        Returns:
            str: File identifier (relative path in POSIX format) of the uploaded content.

        Raises:
            FileNotFoundError: If the parent directory does not exist and `create_parents` is False.
            FileExistsError: If the target already exists and `replace_existing` is False.
            RuntimeError: On upload failure or invalid archive.
        """
        target_path = self.resolve_path(file_id)
        parent_dir = target_path.parent

        if not parent_dir.exists():
            if create_parents:
                parent_dir.mkdir(parents=True, exist_ok=True)
            else:
                raise FileNotFoundError(
                    f"Parent directory does not exist: {parent_dir}"
                )

        if target_path.exists() and not replace_existing:
            raise FileExistsError(f'Target already exists: "{target_path}"')

        # Attempt to rewind file stream if possible
        try:
            file.file.seek(0)
        except Exception:
            pass

        try:
            if is_directory:
                # Expecting a zip file to be extracted into a directory
                zip_extractor = ZipExtractor(file, target_path)
                zip_extractor.extract_using_bytesio()
            else:
                # Upload as a regular file
                with open(target_path, "wb") as out_file:
                    shutil.copyfileobj(file.file, out_file)

        except Exception as e:
            # Clean up if upload partially succeeded
            try:
                if target_path.exists():
                    if target_path.is_dir():
                        shutil.rmtree(target_path)
                    else:
                        target_path.unlink()
            except Exception:
                pass  # Suppress secondary cleanup errors
            raise RuntimeError(f"Upload failed for '{file_id}': {e}")

        return self.get_file_id(target_path)

    def delete(
        self,
        file_id: str,
    ) -> str:
        """
        Delete a file or directory associated with the template.

        Args:
            file_id (str): POSIX-style identifier of the file or directory to delete.

        Returns:
            str: The file identifier that was deleted.

        Raises:
            FileNotFoundError: If the target does not exist.
            RuntimeError: If the path exists but is neither a file nor a directory.
        """
        file_path = self.resolve_path(file_id, must_exist=True)

        if file_path.is_file():
            file_path.unlink()
        elif file_path.is_dir():
            shutil.rmtree(file_path)
        else:
            raise RuntimeError(
                f"Invalid path type: '{file_path}' is not a file or directory."
            )

        return file_id
