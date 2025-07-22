#!/usr/bin/env python

# Copyright (C) 2018 Visual Collaboration Technologies Inc.
# All Rights Reserved.
#
# This file is the property of Visual Collaboration Technologies Inc.
# Unauthorized access, reproduction, or redistribution of any kind is prohibited.
"""
TemplateRuns manages all run runs inside a template's `runs/` directory.

Each run has its own folder (e.g., `runs/default`, `runs/abc`), and
stores its status (`status.json`), configuration (`config/`), diagnostics
(e.g., `diagnostics/execution.log`), and outputs (`outputs/`).
"""

import os
import shutil
import subprocess
from pathlib import Path
from typing import List, Optional

from dotenv import dotenv_values

from vcti.util.short_uid import ShortUID

from .file_names import FileNames
from .run_status import RunState, RunStatus, RunStatusManager


class TemplateRuns:
    def __init__(self, template_path: Path):
        """
        Args:
            template_path (Path): Absolute path to the template directory.
        """
        self._path = template_path
        self._runs_dir = self._path / FileNames.RUNS_DIR
        self._runs_dir.mkdir(exist_ok=True)
        self._initialize_default_run()

    def _initialize_default_run(self):
        default_run_path = self._get_run_path(FileNames.DEFAULT_RUN_ID)
        if not default_run_path.exists():
            self.create_run(FileNames.DEFAULT_RUN_ID)

        active_run_file = self._get_active_run_file_path()
        if not active_run_file.exists():
            self.set_active_run(FileNames.DEFAULT_RUN_ID)

    def get_all_runs(self) -> List[str]:
        """
        Returns a list of all available run IDs under the runs directory.

        Returns:
            List[str]: A list of run IDs (folder names).
        """
        return [d.name for d in self._runs_dir.iterdir() if d.is_dir()]

    def has_run(self, run_id: str) -> bool:
        """
        Checks if a run with the given ID exists.

        Args:
            run_id (str): Run ID to check.

        Returns:
            bool: True if the run exists, False otherwise.
        """
        return self._get_run_path(run_id).exists()

    def _get_active_run_file_path(self) -> Path:
        return self._runs_dir / FileNames.ACTIVE_RUN_FILE

    def _get_run_path(self, run_id: str) -> Path:
        return self._runs_dir / run_id

    def _ensure_run_exists(self, run_id: str):
        self._get_run_path(run_id).mkdir(parents=True, exist_ok=True)

    def get_active_run(self) -> str:
        """
        Returns the currently active run ID.
        """
        path = self._get_active_run_file_path()
        return path.read_text(encoding="utf-8").strip()

    def set_active_run(self, run_id: str) -> None:
        """
        Sets the active run ID for the template.

        Args:
            run_id (str): ID of the run to make active.
        """
        self._ensure_run_exists(run_id)
        self._get_active_run_file_path().write_text(run_id, encoding="utf-8")

    def create_run(self, run_id: Optional[str] = None) -> str:
        """
        Creates a new run directory under `runs/`.

        Args:
            run_id (Optional[str]): Optional run ID. If not given, a unique one is generated.

        Returns:
            str: The created run ID.
        """
        if not run_id:
            run_id = f"{ShortUID.quick()}"

        run_path = self._get_run_path(run_id)
        if run_path.exists():
            raise FileExistsError(f"Run already exists: {run_id}")

        run_path.mkdir(parents=True)
        RunStatusManager(run_path).save(RunStatus(state=RunState.NOT_STARTED))
        return run_id

    def get_run_status(self, run_id: str) -> RunStatus:
        """
        Returns the status of the given run.

        Args:
            run_id (str): Run ID.

        Returns:
            RunStatus: The status object.
        """
        run_path = self._get_run_path(run_id)
        return RunStatusManager(run_path).load()

    def _get_run_process_args(self, run_path: Path) -> list[str]:
        """
        Returns the command-line arguments used to execute the run.

        This method is intended to be overridden in subclasses if a different
        execution process is needed. By default, it runs a dummy sleep command
        for demonstration.

        Args:
            run_path (Path): Absolute path to the run directory.

        Returns:
            List[str]: List of command-line arguments to execute.
        """
        # Placeholder example: Replace with real executable + args as needed
        return ["echo", "hello", "world"]

    def execute_run(self, run_id: Optional[str] = None):
        """
        Starts a run execution by launching a subprocess.

        - Only allowed if run status is NOT_STARTED.
        - Uses environment variables from the run's config/.env file if it exists.
        - Will raise an error if run has already started or completed.

        Args:
            run_id (Optional[str]): Run ID to execute. Defaults to active run.

        Raises:
            RuntimeError: If run status is not NOT_STARTED.
        """
        run_id = run_id or self.get_active_run()
        run_path = self._get_run_path(run_id)
        status_mgr = RunStatusManager(run_path)
        status = status_mgr.load()

        if status.state != RunState.NOT_STARTED:
            raise RuntimeError(
                f"Run '{run_id}' is not in NOT_STARTED state. Current state: {status.state}"
            )

        env_file = run_path / FileNames.CONFIG_DIR / FileNames.ENV_FILE
        env = os.environ.copy()
        if env_file.exists():
            env.update(dotenv_values(env_file))

        process_args = self._get_run_process_args(run_path)

        process = subprocess.Popen(process_args, cwd=run_path, env=env)

        status_mgr.save(RunStatus(state=RunState.RUNNING, pid=process.pid))

    def clear_run(self, run_id: Optional[str] = None):
        """
        Clears run directory contents for a given run if it's not running.

        Args:
            run_id (Optional[str]): Run ID to clear. Defaults to active run.

        Raises:
            RuntimeError: If run is still running.
        """
        run_id = run_id or self.get_active_run()
        run_path = self._get_run_path(run_id)
        status = RunStatusManager(run_path).load()

        if (
            status.state == RunState.RUNNING
            and status.pid
            and self._pid_exists(status.pid)
        ):
            raise RuntimeError(f"Cannot clear running run: {run_id}")

        # Delete contents, preserve the folder
        for item in run_path.iterdir():
            if item.name == "status.json":
                continue  # Preserve status file
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()

        # Reset status
        RunStatusManager(run_path).save(RunStatus(state=RunState.NOT_STARTED))

    def _pid_exists(self, pid: int) -> bool:
        """
        Checks if a process with given PID exists.

        Args:
            pid (int): Process ID to check.

        Returns:
            bool: True if process exists, False otherwise.
        """
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return False
        except PermissionError:
            return True  # Process exists but can't be signaled
        return True
