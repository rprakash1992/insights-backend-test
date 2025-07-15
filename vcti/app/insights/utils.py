#!/usr/bin/env python

# Copyright (C) 2018 Visual Collaboration Technologies Inc.
# All Rights Reserved.
#
# This file is a property of Visual Collaboration Technologies Inc.
# Unauthorized access, reproduction or redistribution of any kind is prohibited.

import datetime
import os
from pathlib import Path
import tempfile
import uuid
import getpass
import platformdirs

from .constants import Constants

def app_data_path():
    return platformdirs.user_data_dir(Constants.APP_NAME, getpass.getuser())

def create_session_directory():
    timestamp_format = "%Y-%m-%d-%H-%M-%S"
    timestamp = datetime.datetime.now().strftime(timestamp_format)
    process_id = os.getpid()
    unique_id = uuid.uuid4().hex[:8]
    dir_name = f"session_{timestamp}_{process_id}_{unique_id}"
    session_dir = Path(tempfile.gettempdir()) / "vcollab-insights" / dir_name
    session_dir.mkdir(parents=True, exist_ok=True)
    os.chdir(str(session_dir))
    return session_dir

def create_env_vars():
    session_dir = create_session_directory()
    os.environ[EnvVar.CURRENT_SESSION_DIR] = str(session_dir)
    profile_dir = ProfileManager.get_active_profile_dir()
    app_data_dir = profile_dir / 'data'
    os.environ[EnvVar.CURRENT_APP_DATA_DIR] = str(app_data_dir)
