#!/usr/bin/env python

# Copyright (C) 2018 Visual Collaboration Technologies Inc.
# All Rights Reserved.
#
# This file is a property of Visual Collaboration Technologies Inc.
# Unauthorized access, reproduction or redistribution of any kind is prohibited.
"""
TemplateFileManager class provides methods to manage files in a template directory.
"""

from fastapi import UploadFile
from pathlib import Path

class ArchiveExtractor:
    def __init__(self, archive: UploadFile, target_dir_path: Path):
        self.archive = archive
        self.target_dir = Path(target_dir_path)

    def extract_using_bytesio(self):
        raise NotImplementedError("Subclasses must implement extract_using_bytesio")

    def extract_using_tempfile(self):
        raise NotImplementedError("Subclasses must implement extract_using_tempfile")

class UnsupportedArchiveFormat(Exception):
    pass