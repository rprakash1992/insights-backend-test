#!/usr/bin/env python

# Copyright (C) 2018 Visual Collaboration Technologies Inc.
# All Rights Reserved.
#
# This file is a property of Visual Collaboration Technologies Inc.
# Unauthorized access, reproduction or redistribution of any kind is prohibited.

def get_var(name):
    return f"VCOLLAB_INSIGHTS_{name.upper()}"

class EnvVar:
    APP_NAME = get_var("app_name")
    SYNC_TO_ORIGIN_ON_EXIT = get_var("repo_sync_to_origin_on_exit")
    DEFAULT_REMOTE_TEMPLATES_REPO = get_var("templates_remote_repo")
    DEFAULT_LOCAL_TEMPLATES_PATH = get_var("templates_local_path")
    DEFAULT_PROFILES_PATH = get_var("default_profiles_path")
    CURRENT_SESSION_DIR = get_var("current_session_dir")
    CURRENT_PROFILE_DIR = get_var("current_profile_dir")
    CURRENT_APP_DATA_DIR = get_var("current_app_data_dir")
    STAIC_FILES_FOLDER = get_var("static_files_folder")