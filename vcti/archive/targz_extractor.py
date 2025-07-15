#!/usr/bin/env python

# Copyright (C) 2018 Visual Collaboration Technologies Inc.
# All Rights Reserved.
#
# This file is a property of Visual Collaboration Technologies Inc.
# Unauthorized access, reproduction or redistribution of any kind is prohibited.
"""
TemplateFileManager class provides methods to manage files in a template directory.
"""

import zipfile
from pathlib import Path
from io import BytesIO
from tempfile import NamedTemporaryFile
from fastapi import UploadFile
import shutil
import tarfile

from .extrctor_base import ArchiveExtractor, UnsupportedArchiveFormat


class TarGzExtractor(ArchiveExtractor):
    def __init__(self, archive: UploadFile, target_dir_path: Path):
        super().__init__(archive, target_dir_path)

    def extract_using_bytesio(self):
        self.archive.file.seek(0)
        with BytesIO(self.archive.file.read()) as buffer:
            with tarfile.open(fileobj=buffer, mode="r:gz") as tar_ref:
                tar_ref.extractall(self.target_dir)

    def extract_using_tempfile(self):
        self.archive.file.seek(0)
        with NamedTemporaryFile(delete=True, suffix=".tar.gz") as tmp:
            shutil.copyfileobj(self.archive.file, tmp)
            tmp.flush()
            tmp.seek(0)
            with tarfile.open(tmp.name, mode="r:gz") as tar_ref:
                tar_ref.extractall(self.target_dir)
