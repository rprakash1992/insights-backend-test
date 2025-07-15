#!/usr/bin/env python

# Copyright (C) 2018 Visual Collaboration Technologies Inc.
# All Rights Reserved.
#
# This file is a property of Visual Collaboration Technologies Inc.
# Unauthorized access, reproduction or redistribution of any kind is prohibited.

import os
from pathlib import Path
from typing import Any, Dict, Optional, Union
from git import Repo
import git.exc
import shutil

class GitRepositoryManager:
    """
    Handles Git repository operations including remote management.
    
    This class encapsulates all Git repository-specific operations,
    separating them from template management logic.
    """

    def __init__(self, local_repo_path: Union[str, Path]):
        """
        Initialize with a local repository path.
        
        Args:
            local_repo_path: Path to the local Git repository
        """
        self._local_repo_path = Path(local_repo_path).expanduser().resolve()
        self._repo = None  # Lazily initialized

    @property
    def directory_path(self) -> Path:
        return self._local_repo_path

    @property
    def _git_repo(self) -> Repo:
        """Lazy-loaded GitPython Repo instance"""
        if self._repo is None:
            if not self.is_valid_repository():
                raise ValueError(f"Not a valid Git repository: {self._local_repo_path}")
            self._repo = Repo(self._local_repo_path)
        return self._repo

    def is_valid_repository(self) -> bool:
        """
        Check if the configured path contains a valid Git repository.
    
        Returns:
            bool: True if valid repository exists, False otherwise
        """
        try:
            return bool(
                self._local_repo_path.exists() 
                and Repo(self._local_repo_path).git_dir
            )
        except git.exc.InvalidGitRepositoryError:
            return False

    def create_from_remote(
        self,
        remote_url: str,
        overwrite: bool = False
    ) -> Path:
        """
        Clone a remote repository to the local path.
        
        Args:
            remote_url: URL of the remote repository
            overwrite: If True, overwrite existing directory
            
        Returns:
            Path to the cloned repository
            
        Raises:
            ValueError: If local path exists and overwrite=False
            git.exc.GitCommandError: If clone fails
        """
        if self._local_repo_path.exists():
            if not overwrite:
                raise ValueError(f"Path already exists: {self._local_repo_path}")
            shutil.rmtree(self._local_repo_path)

        try:
            Repo.clone_from(remote_url, self._local_repo_path)
            return self._local_repo_path
        except git.exc.GitCommandError as e:
            if self._local_repo_path.exists():
                shutil.rmtree(self._local_repo_path)
            raise RuntimeError(f"Clone failed: {str(e)}") from e

    def commit_changes(self, message: str = "Update") -> None:
        """
        Commit all changes in the repository.
        
        Args:
            message: Commit message
            
        Raises:
            git.exc.GitCommandError: If commit fails
        """
        self._git_repo.index.commit(message)

    def list_remotes(self) -> Dict[str, str]:
        """
        List all configured remotes and their URLs.
        
        Returns:
            Dictionary mapping remote names to URLs
            
        Example:
            {'origin': 'https://github.com/user/repo.git'}
        """
        return {remote.name: next(remote.urls) for remote in self._git_repo.remotes}

    def add_remote(
        self,
        name: str,
        url: str,
        fetch: bool = True
    ) -> None:
        """
        Add a new remote repository.
        
        Args:
            name: Name for the new remote
            url: Remote repository URL
            fetch: Whether to fetch from the remote immediately
            
        Raises:
            ValueError: If remote already exists
            git.exc.GitCommandError: If operation fails
        """
        if name in [r.name for r in self._git_repo.remotes]:
            raise ValueError(f"Remote '{name}' already exists")
        
        remote = self._git_repo.create_remote(name, url)
        if fetch:
            remote.fetch()

    def remove_remote(self, name: str) -> None:
        """
        Remove a configured remote repository.
    
        Args:
            name: Name of the remote to remove
        
        Raises:
            ValueError: If remote doesn't exist
            git.exc.GitCommandError: If removal fails
        
        Example:
            >>> remove_remote("upstream")
        """
        remote = None
        # Find the remote object by name
        for r in self._git_repo.remotes:
            if r.name == name:
                remote = r
                break
    
        if not remote:
            available = [r.name for r in self._git_repo.remotes]
            raise ValueError(
                f"Remote '{name}' does not exist. "
                f"Available remotes: {available}"
            )
    
        self._git_repo.delete_remote(remote)

    def fetch_from_remote(
        self,
        remote_name: str = "origin",
        fetch_args: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Fetch updates from a remote repository with customizable arguments.
    
        Args:
            remote_name: Name of remote to fetch from (default: "origin")
            fetch_args: Additional git fetch arguments as key-value pairs.
                   Common options:
                   - 'tags': bool (fetch all tags)
                   - 'prune': bool (remove stale remote references)
                   Example: {'tags': True, 'prune': True}
                   
        Raises:
            ValueError: If remote doesn't exist
            git.exc.GitCommandError: If fetch fails
        
        Example:
            >>> fetch_from_remote("upstream", {'tags': True})
        """
        if remote_name not in [r.name for r in self._git_repo.remotes]:
            raise ValueError(f"Remote '{remote_name}' does not exist. Available remotes: {list(self._git_repo.remotes)}")
    
        remote = self._git_repo.remote(name=remote_name)
        remote.fetch(**(fetch_args or {}))

    def push_to_remote(
        self,
        remote_name: str = "origin",
        branch: str = "main",
        push_args: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Push changes to a remote repository with customizable arguments.
    
        Args:
            remote_name: Name of remote to push to (default: "origin")
            branch: Branch to push (default: "main")
            push_args: Additional git push arguments as key-value pairs.
                   Common options:
                   - 'force': bool (force push)
                   - 'atomic': bool (atomic push)
                   Example: {'force': True}
                   
        Raises:
            ValueError: If remote doesn't exist
            git.exc.GitCommandError: If push fails
        
        Example:
            >>> push_to_remote("origin", "main", {'force': True})
        """
        if remote_name not in [r.name for r in self._git_repo.remotes]:
            raise ValueError(f"Remote '{remote_name}' does not exist. Available remotes: {list(self._git_repo.remotes)}")
    
        remote = self._git_repo.remote(name=remote_name)
        remote.push(refspec=f"{branch}", **(push_args or {}))