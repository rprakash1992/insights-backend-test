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
from io import BytesIO
from typing import Iterator, Optional

class DirectoryZipMemoryStreamer:
    """
    A memory-efficient streaming ZIP generator for directory contents.
    
    This class creates a ZIP archive of a directory structure on-the-fly without loading
    the entire contents into memory. It yields chunks of ZIP data as they become available.

    Typical Usage:
        >>> streamer = DirectoryZipMemoryStreamer(Path("/path/to/directory"))
        >>> StreamingResponse(streamer, media_type="application/zip")

    Attributes:
        chunk_size (int): Number of bytes to yield per chunk (default: 64KB)
    """

    def __init__(self, directory_path: Path, chunk_size: int = 65536) -> None:
        """
        Initialize the ZIP streamer for a directory.

        Args:
            directory_path: Path to the directory to be zipped
            chunk_size: Size of data chunks to yield (in bytes)

        Raises:
            ValueError: If directory_path doesn't exist or isn't a directory
        """
        if not directory_path.is_dir():
            raise ValueError(f"Path is not a directory: {directory_path}")
        
        self.directory_path = directory_path.resolve()
        self.chunk_size = chunk_size
        self._buffer = BytesIO()
        self._zip_file = zipfile.ZipFile(self._buffer, 'w', zipfile.ZIP_DEFLATED)
        self._file_iterator = self._generate_file_paths()

    def _generate_file_paths(self) -> Iterator[Path]:
        """
        Generator yielding all files in the directory tree.

        Yields:
            Path objects for each file in the directory hierarchy

        Raises:
            RuntimeError: If directory traversal fails
        """
        try:
            for root, _, files in os.walk(self.directory_path):
                for filename in files:
                    yield Path(root) / filename
        except Exception as e:
            raise RuntimeError(f"Directory traversal failed: {str(e)}") from e

    def _add_file_to_zip(self, file_path: Path) -> Optional[bytes]:
        """
        Add a single file to the ZIP and return available chunks.

        Args:
            file_path: Path to the file to add

        Returns:
            bytes or None: ZIP data if buffer contains enough for a chunk

        Raises:
            RuntimeError: If file operations fail
        """
        try:
            arcname = file_path.relative_to(self.directory_path)
            self._zip_file.write(file_path, arcname)
            self._zip_file.fp.flush()  # Force write to buffer
            return self._get_available_chunk()
        except Exception as e:
            raise RuntimeError(f"Failed adding {file_path} to ZIP: {str(e)}") from e

    def _get_available_chunk(self) -> Optional[bytes]:
        """Extract a chunk from buffer if enough data is available."""
        self._buffer.seek(0)
        if self._buffer.getbuffer().nbytes >= self.chunk_size:
            chunk = self._buffer.read(self.chunk_size)
            self._buffer.seek(0)
            self._buffer.truncate()
            return chunk
        return None

    def __iter__(self) -> Iterator[bytes]:
        """
        Main generator interface that yields ZIP data chunks.

        Yields:
            bytes: Chunks of ZIP file data

        Raises:
            RuntimeError: If ZIP creation fails at any point

        Note:
            Always closes the ZIP file properly, even if generation is interrupted.
        """
        try:
            # Process files and yield chunks as they become available
            for file_path in self._file_iterator:
                if chunk := self._add_file_to_zip(file_path):
                    yield chunk

            # Yield remaining data and close
            self._zip_file.close()
            self._buffer.seek(0)
            while remaining := self._buffer.read(self.chunk_size):
                yield remaining

        except Exception as e:
            self._zip_file.close()
            raise RuntimeError(f"ZIP streaming failed: {str(e)}") from e
        finally:
            self._buffer.close()