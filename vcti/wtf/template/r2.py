from __future__ import annotations

import json
import os
import shutil
import subprocess
from enum import StrEnum
from pathlib import Path
from typing import Optional

from pydantic import BaseModel

from ..file_names import FileNames
from ..job_status import JobStatus
from ..utils.env_utils import read_env_file


class JobStatusModel(BaseModel):
    status: JobStatus
    pid: Optional[int] = None


class TemplateRuns:
    """
    Manages execution runs for a template.
    Each run is represented by a folder under the 'runs' directory.
    """

    def __init__(self, path: Path):
        self._path = path
        self._runs_dir = self._path / FileNames.RUNS_DIR
        self._runs_dir.mkdir(exist_ok=True)
        self._active_file = self._runs_dir / ".active"
        self._initialize_default_job()

    def _initialize_default_job(self):
        default_path = self._runs_dir / FileNames.DEFAULT_JOB
        default_path.mkdir(exist_ok=True)
        if not self._active_file.exists():
            self.set_active_job(FileNames.DEFAULT_JOB)

    def get_all_runs(self) -> list[str]:
        """
        Returns a list of all available job IDs under the runs directory.

        Returns:
            list[str]: A list of job IDs (folder names).
        """
        return [d.name for d in self._runs_dir.iterdir() if d.is_dir()]

    def get_active_job(self) -> str:
        """
        Returns the ID of the currently active job.

        Returns:
            str: Active job ID.
        """
        return self._active_file.read_text(encoding="utf-8").strip()

    def get_job_status(self, job_id: str) -> JobStatusModel:
        """
        Retrieves the status of a given job.

        Args:
            job_id (str): Job identifier.

        Returns:
            JobStatusModel: The current status and process ID (if any).
        """
        job_dir = self._runs_dir / job_id
        status_file = job_dir / FileNames.STATUS_JSON
        if not status_file.exists():
            return JobStatusModel(status=JobStatus.NOT_STARTED)

        data = json.loads(status_file.read_text(encoding="utf-8"))
        job_status = JobStatus(data.get("status", JobStatus.NOT_STARTED))
        pid = data.get("pid")

        if job_status == JobStatus.RUNNING:
            if pid is None or not self._pid_exists(pid):
                # Check diagnostics for success marker
                diagnostics_dir = job_dir / "diagnostics"
                marker = diagnostics_dir / "execution.ok"
                job_status = (
                    JobStatus.COMPLETED if marker.exists() else JobStatus.FAILED
                )

        return JobStatusModel(status=job_status, pid=pid)

    def create_job(self, job_id: str):
        """
        Creates a new job directory under runs.

        Args:
            job_id (str): New job identifier.

        Raises:
            FileExistsError: If a job with the same ID already exists.
        """
        job_dir = self._runs_dir / job_id
        if job_dir.exists():
            raise FileExistsError(f"Job '{job_id}' already exists.")
        job_dir.mkdir(parents=True)

    def set_active_job(self, job_id: str):
        """
        Sets the active job.

        Args:
            job_id (str): Job ID to set as active.

        Raises:
            FileNotFoundError: If the specified job directory does not exist.
        """
        job_dir = self._runs_dir / job_id
        if not job_dir.exists():
            raise FileNotFoundError(f"Job '{job_id}' does not exist.")
        self._active_file.write_text(job_id, encoding="utf-8")

    def execute_job(self, job_id: str):
        """
        Executes the specified job. Fails if job is already running or not cleared.

        Args:
            job_id (str): Job to execute.

        Raises:
            RuntimeError: If job is not in NOT_STARTED state.
        """
        job_status = self.get_job_status(job_id)
        if job_status.status != JobStatus.NOT_STARTED:
            raise RuntimeError(f"Cannot execute job in state: {job_status.status}")

        job_dir = self._runs_dir / job_id
        status_file = job_dir / FileNames.STATUS_JSON
        diagnostics_dir = job_dir / "diagnostics"
        diagnostics_dir.mkdir(exist_ok=True)

        args = self._job_process_arguments(job_id)
        env_file = job_dir / "config" / ".env"
        env = os.environ.copy()
        if env_file.exists():
            env.update(read_env_file(env_file))

        process = subprocess.Popen(
            args,
            cwd=job_dir,
            env=env,
            stdout=open(diagnostics_dir / "execution.log", "w"),
            stderr=subprocess.STDOUT,
        )

        status_file.write_text(
            json.dumps({"status": JobStatus.RUNNING, "pid": process.pid}, indent=2),
            encoding="utf-8",
        )

    def clear_job(self, job_id: str):
        """
        Clears job directory content if not currently running.

        Args:
            job_id (str): Job ID to clear.

        Raises:
            RuntimeError: If job is currently running.
        """
        job_status = self.get_job_status(job_id)
        if job_status.status == JobStatus.RUNNING:
            raise RuntimeError(f"Cannot clear job '{job_id}' while it is running.")

        job_dir = self._runs_dir / job_id
        for child in job_dir.iterdir():
            if child.is_dir():
                shutil.rmtree(child)
            else:
                child.unlink()

    def _job_process_arguments(self, job_id: str) -> list[str]:
        """
        Returns the command-line arguments used to execute the job.

        Args:
            job_id (str): The job identifier.

        Returns:
            List[str]: Arguments for subprocess execution.
        """
        return ["python", "main.py"]

    def _pid_exists(self, pid: int) -> bool:
        """
        Check if a process with the given PID exists.

        Args:
            pid (int): Process ID to check.

        Returns:
            bool: True if the process exists, False otherwise.
        """
        try:
            os.kill(pid, 0)
        except OSError:
            return False
        return True
