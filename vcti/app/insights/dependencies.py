#!/usr/bin/env python

# Copyright (C) 2018 Visual Collaboration Technologies Inc.
# All Rights Reserved.
#
# This file is a property of Visual Collaboration Technologies Inc.
# Unauthorized access, reproduction or redistribution of any kind is prohibited.

import logging
import os
from pathlib import Path
import shutil

from vcti.app_data.directory import AppDataDir
from vcti.app_data.profile_manager import ProfileManager
from vcti.wtf.template.repository import TemplatesRepository
from vcti.wtf.env_vars import EnvVar
from vcti.util.env_value import EnvValueDecoder


ENV_PREFIX="VCOLLAB_INSIGHTS_"


TEMPLATES_REPOSITORY = None
STATIC_FOLDER_PATH = None


logger = logging.getLogger('uvicorn.info')

def setup():
    global TEMPLATES_REPOSITORY
    global STATIC_FOLDER_PATH
    with AppDataDir(env_prefix=ENV_PREFIX).context() as app_data_ctx:
        logging.info('Using application data folder: "%s"', app_data_ctx.path)
        profile_manager = ProfileManager(env_prefix=ENV_PREFIX)
        logging.info('Profiles directory path: "%s%', profile_manager.path)
        profile_manager.initialize()

        active_profile = profile_manager.get_active_profile()
        profile_dir = profile_manager.get_profile_dir(active_profile)
        TEMPLATES_REPOSITORY = TemplatesRepository(parent_dir=profile_dir)
        TEMPLATES_REPOSITORY.initialize()

        STATIC_FOLDER_PATH = EnvValueDecoder.get_string(EnvVar.STAIC_FILES_FOLDER)
        if not STATIC_FOLDER_PATH:
            STATIC_FOLDER_PATH = profile_dir / 'static'
            if not STATIC_FOLDER_PATH.exists():
                base_path = os.path.dirname(__file__)
                static_source_dir = Path(base_path) / "static"
                shutil.copytree(static_source_dir, STATIC_FOLDER_PATH)

def shutdown():
    pass


def templates_repository():
    global TEMPLATES_REPOSITORY
    return TEMPLATES_REPOSITORY


def static_folder_path():
    global STATIC_FOLDER_PATH
    return STATIC_FOLDER_PATH


#def commit_session_changes():
#    commit_message = "Commit Session Updates."
#    sync_to_origin = EnvValueDecoder().get_flag(
#            EnvVar.SYNC_TO_ORIGIN_ON_EXIT, default=False)
#    TEMPLATES_REPOSITORY.commit_changes(
#        commit_message,
#        sync_to_origin
#    )
#    global TEMPLATES_REPOSITORY