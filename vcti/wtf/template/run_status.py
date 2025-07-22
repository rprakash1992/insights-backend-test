#!/usr/bin/env python

# Copyright (C) 2018 Visual Collaboration Technologies Inc.
# All Rights Reserved.
#
# This file is the property of Visual Collaboration Technologies Inc.
# Unauthorized access, reproduction, or redistribution of any kind is prohibited.
"""
RunStatusManager handles reading and writing run status information
to a `status.json` file at the root of a run directory.
"""

import json
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field

from vcti.util.value_generated_enums import EnumValueSameAsName, auto_enum_value

from .file_names import FileNames


class RunState(EnumValueSameAsName):
    NOT_STARTED = auto_enum_value()
    RUNNING = auto_enum_value()
    COMPLETED = auto_enum_value()
    FAILED = auto_enum_value()


class RunStatus(BaseModel):
    """
    Represents the status of a single run run.

    Attributes:
        state (RunState): Current state of the run.
        pid (Optional[int]): Process ID if the run is running.
        message (Optional[str]): Additional context or error message.
    """

    state: RunState = Field(default=RunState.NOT_STARTED)
    pid: Optional[int] = None
    message: Optional[str] = None


class RunStatusManager:
    """
    Manages run status persistence using a `status.json` file.

    Example usage:
        run_status = RunStatusManager(run_dir)
        current = run_status.load()
        run_status.save(RunStatus(state=RunState.RUNNING, pid=12345))
    """

    def __init__(self, run_dir: Path):
        """
        Args:
            run_dir (Path): Path to the root directory of the run.
        """
        self.run_dir = run_dir
        self.status_file = run_dir / FileNames.RUN_STATUS_FILE

    def exists(self) -> bool:
        """Returns True if the status file exists."""
        return self.status_file.exists()

    def load(self) -> RunStatus:
        """
        Loads the run status from the status file.

        Returns:
            RunStatus: Parsed status object. Defaults to NOT_STARTED if missing or corrupt.
        """
        if not self.status_file.exists():
            return RunStatus()

        try:
            data = json.loads(self.status_file.read_text(encoding="utf-8"))
            return RunStatus(**data)
        except Exception:
            return RunStatus()  # fallback to default if parsing fails

    def save(self, status: RunStatus) -> None:
        """
        Saves the run status to the status file.

        Args:
            status (RunStatus): The status to save.
        """
        self.status_file.write_text(status.model_dump_json(indent=2), encoding="utf-8")

    def update(
        self,
        state: Optional[RunState] = None,
        pid: Optional[int] = None,
        message: Optional[str] = None,
    ) -> None:
        """
        Updates one or more fields in the run status.

        Args:
            state (Optional[RunState]): New run state, if specified.
            pid (Optional[int]): Process ID, if specified.
            message (Optional[str]): Status message, if specified.
        """
        current_status = self.load()

        if state is not None:
            current_status.state = state
        if pid is not None:
            current_status.pid = pid
        if message is not None:
            current_status.message = message

        self.save(current_status)
