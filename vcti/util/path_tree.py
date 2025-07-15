#!/usr/bin/env python

# Copyright (C) 2018 Visual Collaboration Technologies Inc.
# All Rights Reserved.
#
# This file is a property of Visual Collaboration Technologies Inc.
# Unauthorized access, reproduction or redistribution of any kind is prohibited.

from pathlib import Path
from typing import List, Optional, Union
from pydantic import BaseModel

from .value_generated_enums import EnumValueLowerCase, auto_enum_value

class PathType(EnumValueLowerCase):
    FILE = auto_enum_value()
    DIRECTORY = auto_enum_value()


class PathBase(BaseModel):
    name: str
    path: str
    type: PathType


class File(PathBase):
    size: int
    type: PathType = PathType.FILE


class Directory(PathBase):
    children: List[Union['Directory', File]] = []
    type: PathType = PathType.DIRECTORY


Directory.model_rebuild()


def handle_file(
    path_obj: Path,
    base_path: Optional[Path] = None,
    as_posix: bool = False
) -> File:
    """Create a File model from a Path object."""
    path_val = (
        path_obj.relative_to(base_path)
        if base_path
        else path_obj
    )
    if as_posix:
        path_val = path_val.as_posix()
    return File(
        name=path_obj.name,
        path=str(path_val),
        size=path_obj.stat().st_size
    )

def handle_directory(
    path_obj: Path,
    base_path: Optional[Path] = None,
    as_posix: bool = False
) -> Directory:
    """Create a Directory model, recursively including children."""
    path_val = (
        path_obj.relative_to(base_path)
        if base_path
        else path_obj
    )
    if as_posix:
        path_val = path_val.as_posix()

    dir_item = Directory(
        name=path_obj.name,
        path=str(path_val),
        children=[]
    )
    for child in sorted(path_obj.iterdir()):
        if child.is_file():
            dir_item.children.append(handle_file(child, base_path, as_posix))
        else:
            dir_item.children.append(handle_directory(child, base_path, as_posix))
    return dir_item


PathTree = List[Union[Directory, File]]


def get_path_tree(
    path: Path,
    base_path: Optional[Path] = None,  # None → full paths; non-None → relative to base_path
    as_posix: bool = False,
    skip_root: bool = False
) -> PathTree:
    """
    Returns folder structure as list of Pydantic models.

    Args:
        path: File or directory path to scan.
        as_posix: If True, forces forward slashes in paths.
        skip_root: If True, returns only children (empty list for files).
        base_path: If provided, paths are stored relative to this directory.
                  If None, absolute paths are stored.

    Returns:
        List of Directory/File objects
    """
    if not path.exists():
        return []

    if path.is_file():
        file_item = handle_file(path, base_path, as_posix)
        return [] if skip_root else [file_item]

    # Directory
    dir_item = handle_directory(path, base_path, as_posix)
    return dir_item.children if skip_root else [dir_item]


def _cli_tree_lines(node, prefix=""):
    lines = []
    connector = "├── "
    last_connector = "└── "
    if isinstance(node, Directory):
        lines.append(f"{prefix}{node.name}/")
        child_count = len(node.children)
        for idx, child in enumerate(node.children):
            is_last = idx == child_count - 1
            next_prefix = prefix + ("    " if is_last else "│   ")
            child_connector = last_connector if is_last else connector
            lines.extend(_cli_tree_lines(child, prefix + child_connector))
    else:
        lines.append(f"{prefix}{node.name}")
    return lines


def get_cli_tree(path_tree: PathTree):
    lines = []
    for node in path_tree:
        lines.extend(_cli_tree_lines(node))
    return lines

