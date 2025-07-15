#!/usr/bin/env python

# Copyright (C) 2018 Visual Collaboration Technologies Inc.
# All Rights Reserved.
#
# This file is a property of Visual Collaboration Technologies Inc.
# Unauthorized access, reproduction or redistribution of any kind is prohibited.

import os
from enum import StrEnum

class ConfigVariable(StrEnum):
    APP_AUTHOR = 'VCollab'
    APP_NAME = 'Insights'
    PROFILES_DIR = 'profiles'


class ConfigValue:
    def __init__(self, env_prefix: str = ""):
        self.env_prefix = env_prefix

    def value(self, var: ConfigVariable) -> str:
        env_value = os.getenv(f'{self.env_prefix}{var.name}')
        if env_value is not None:
            return env_value
        else:
            return var.value
