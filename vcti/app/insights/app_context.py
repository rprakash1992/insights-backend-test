#!/usr/bin/env python

# Copyright (C) 2018 Visual Collaboration Technologies Inc.
# All Rights Reserved.
#
# This file is a property of Visual Collaboration Technologies Inc.
# Unauthorized access, reproduction or redistribution of any kind is prohibited.

import logging
import shutil
from pathlib import Path

from vcti.app_data.directory import AppDataDirectory
from vcti.app_data.profile_manager import ProfileManager
from vcti.wtf.app_environment import AppEnvironment
from vcti.wtf.template.repository import TemplatesRepository

TEMPLATES_REPOSITORY = None
STATIC_FILES_DIRECTORY = None


logger = logging.getLogger("uvicorn.info")


def setup():
    global TEMPLATES_REPOSITORY
    global STATIC_FILES_DIRECTORY

    # Execute under the application data directory context
    with AppDataDirectory(AppEnvironment.app_data_dir.value).context() as app_data_ctx:
        logging.info('Using application data folder: "%s"', app_data_ctx.path)

        # Create and initialize the profile manager
        profile_manager = ProfileManager(AppEnvironment.profiles_path.value)
        logging.info('Profiles directory path: "%s"', profile_manager.path)
        profile_manager.initialize()

        # Get the active profile and its directory
        active_profile = profile_manager.get_active_profile()
        profile_dir = profile_manager.get_profile_dir(active_profile)

        # Set up template repository under the active profile directory
        TEMPLATES_REPOSITORY = TemplatesRepository(
            local_repo_path=AppEnvironment.templates_local_path.value,
            remote_repo_url=AppEnvironment.templates_remote_repo.value,
        )

        # Get the static files directory from environment or default to profile/static
        default_static_path = profile_dir / "static"
        STATIC_FILES_DIRECTORY = AppEnvironment.static_files_dir.value
        if not STATIC_FILES_DIRECTORY.is_absolute():
            STATIC_FILES_DIRECTORY = profile_dir / STATIC_FILES_DIRECTORY

        # If static files folder doesn't exist, copy from the built-in source
        if not STATIC_FILES_DIRECTORY.exists():
            shutil.copytree(get_package_static_source(), STATIC_FILES_DIRECTORY)


def get_package_static_source() -> Path:
    """Get the source directory for static files."""
    base_path = Path(__file__).parent
    return base_path / "static"


def shutdown():
    """Clean up resources on shutdown."""
    pass


def templates_repository():
    """Get the templates repository instance."""
    global TEMPLATES_REPOSITORY
    return TEMPLATES_REPOSITORY


def static_files_directory():
    """Get the path to the static files folder."""
    global STATIC_FILES_DIRECTORY
    return STATIC_FILES_DIRECTORY
