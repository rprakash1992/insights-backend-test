#!/usr/bin/env python

# Copyright (C) 2018 Visual Collaboration Technologies Inc.
# All Rights Reserved.
#
# This file is a property of Visual Collaboration Technologies Inc.
# Unauthorized access, reproduction or redistribution of any kind is prohibited.
"""VCollab Insights application environment."""

from pathlib import Path
from typing import ClassVar

import platformdirs

from vcti.util.app_environment import AppEnvironmentBase, Variable, VariableType


class AppEnvironment(AppEnvironmentBase):
    ENV_PREFIX: ClassVar[str] = "VCOLLAB_INSIGHTS_"

    app_name: Variable = Variable(VariableType.STRING, default="VCollab Insights")
    app_author: Variable = Variable(VariableType.STRING, default="VCollab")
    app_data_dir: Variable = Variable(
        VariableType.PATH,
        default=Path(platformdirs.user_data_dir("VCollab Insights", "VCollab")),
    )
    profiles_path: Variable = Variable(VariableType.PATH, default=Path("profiles"))
    static_files_dir: Variable = Variable(VariableType.PATH, default="static")
    repo_sync_to_origin_on_exit: Variable = Variable(VariableType.FLAG, default=False)
    templates_remote_repo: Variable = Variable(
        VariableType.STRING,
        default="https://github.com/vctmohan/insights-templates-library-example.git",
    )
    templates_local_path: Variable = Variable(
        VariableType.PATH, default=Path("templates")
    )
    current_session_dir: Variable = Variable(
        VariableType.PATH, default=Path("sessions/current")
    )
    current_profile_dir: Variable = Variable(
        VariableType.PATH, default=Path("profiles/current")
    )
    current_app_data_dir: Variable = Variable(
        VariableType.PATH, default=Path("app_data/current")
    )
