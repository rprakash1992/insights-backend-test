#!/usr/bin/env python

# Copyright (C) 2018 Visual Collaboration Technologies Inc.
# All Rights Reserved.
#
# This file is a property of Visual Collaboration Technologies Inc.
# Unauthorized access, reproduction or redistribution of any kind is prohibited.
"""
A memory-efficient streaming ZIP generator for directory contents.
"""

import os
import zipfile
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Iterator
from fastapi import BackgroundTasks
from fastapi.responses import StreamingResponse

class LargeDirectoryZipStreamer:
    """
    A ZIP streamer that uses temporary files for memory-efficient large archive generation.
    Automatically cleans up temp files using FastAPI's BackgroundTasks.

    Ideal for large directories where memory usage is a concern.

    Usage:
        >>> streamer = LargeDirectoryZipStreamer(
        >>>     folder_path=Path("/data/project"),
        >>>     archive_name="project.zip",
        >>>     background_tasks=background_tasks
        >>> )
        >>> return StreamingResponse(
        >>>     streamer.stream(),
        >>>     media_type="application/zip",
        >>>     headers={"Content-Disposition": f"attachment; filename={streamer.archive_name}"}
        >>> )
    """

    def __init__(
        self,
        folder_path: Path,
        archive_name: str,
        background_tasks: BackgroundTasks,
        chunk_size: int = 65536
    ):
        """
        Initialize the temp file ZIP streamer.

        Args:
            folder_path: Path to the directory to zip
            archive_name: Name for the output ZIP file
            background_tasks: FastAPI BackgroundTasks for cleanup
            chunk_size: Read chunk size in bytes (default: 64KB)
        """
        self.folder_path = folder_path.resolve()
        self.archive_name = archive_name
        self.background_tasks = background_tasks
        self.chunk_size = chunk_size
        self._temp_file = None

    def _generate_zip(self) -> Path:
        """Create the ZIP file in a temp location."""
        try:
            # Create temp file with delete=False so we can control deletion
            with NamedTemporaryFile(delete=False, suffix='.zip') as tmp:
                temp_path = Path(tmp.name)
            
            # Build the ZIP archive
            with zipfile.ZipFile(temp_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, _, files in os.walk(self.folder_path):
                    for file in files:
                        file_path = Path(root) / file
                        arcname = file_path.relative_to(self.folder_path)
                        zipf.write(file_path, arcname)
            
            return temp_path
        except Exception as e:
            if temp_path.exists():
                temp_path.unlink(missing_ok=True)
            raise RuntimeError(f"ZIP creation failed: {str(e)}") from e

    def _stream_chunks(self, zip_path: Path) -> Iterator[bytes]:
        """
        Generator that yields chunks of the ZIP file.
        Ensures temp file cleanup when done.
        """
        try:
            with open(zip_path, 'rb') as f:
                while chunk := f.read(self.chunk_size):
                    yield chunk
        finally:
            # Schedule cleanup via background tasks
            self.background_tasks.add_task(
                self._cleanup_temp_file,
                zip_path
            )

    def _cleanup_temp_file(self, path: Path):
        """Safely remove the temp file."""
        try:
            if path.exists():
                path.unlink()
        except Exception as e:
            # Log error but don't fail
            pass

    def stream(self) -> Iterator[bytes]:
        """
        Main streaming interface.
        
        Returns:
            Iterator that yields ZIP file chunks
            
        Raises:
            RuntimeError: If ZIP creation fails
            FileNotFoundError: If source folder doesn't exist
        """
        if not self.folder_path.exists():
            raise FileNotFoundError(f"Folder not found: {self.folder_path}")

        zip_path = self._generate_zip()
        return self._stream_chunks(zip_path)

    def as_response(self) -> StreamingResponse:
        """
        Convenience method to create a full StreamingResponse.
        
        Returns:
            StreamingResponse: Configured response with:
              - Correct media type
              - Content-Disposition header
              - Background cleanup
        """
        return StreamingResponse(
            content=self.stream(),
            media_type="application/zip",
            headers={
                "Content-Disposition": f"attachment; filename={self.archive_name}",
                "Content-Length": str(os.path.getsize(self._temp_file)) if self._temp_file else None
            }
        )