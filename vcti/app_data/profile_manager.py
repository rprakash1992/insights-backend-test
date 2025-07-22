#!/usr/bin/env python

# Copyright (C) 2018 Visual Collaboration Technologies Inc.
# All Rights Reserved.
#
# This file is a property of Visual Collaboration Technologies Inc.
# Unauthorized access, reproduction or redistribution of any kind is prohibited.
"""
ProfileManager provides methods to manage template repositories and profiles.

The manager handles:
- Profile creation, deletion, and listing
- Active profile management
- Profile information storage and retrieval
- Profile directory structure management
"""

import json
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .profile import DEFAULT_PROFILE, Profile, ProfileInfo, ProfileList

PROFILE_INFO_FILE_NAME = "profile-info.json"
ACTIVE_PROFILE_FILE_NAME = ".active-profile"


class ProfileManager:
    """Manages creation, deletion, and organization of profiles."""

    def __init__(self, dir_path: Union[str, Path]) -> None:
        """
        Initialize the ProfileManager.

        Args:
            dir_path: Profiles directory path. This can be an absolute path or relative to the current working directory.

        Raises:
            ValueError: If neither profiles_dir nor default config is available.
        """
        self._dir_path = Path(dir_path).expanduser().resolve()
        self._dir_path.mkdir(parents=True, exist_ok=True)
        self._active_profile_file_path = self._dir_path / ACTIVE_PROFILE_FILE_NAME
        self.initialize()

    @property
    def path(self) -> Path:
        """Get the base directory path for profiles."""
        return self._dir_path

    def initialize(self) -> None:
        """Initialize the profiles directory structure with defaults."""
        # Create default profile if it doesn't exist
        if not self.profile_exists(DEFAULT_PROFILE.id):
            self._create_profile(DEFAULT_PROFILE)

        # Initialize active-profile file if it doesn't exist
        if not self._active_profile_file_path.exists():
            self.set_active_profile(DEFAULT_PROFILE.id)

    def profile_exists(self, id: str) -> bool:
        """Check if a profile with the given ID exists."""
        return (self._dir_path / id).exists()

    def get_profile_dir(self, id: str) -> Path:
        """Get the directory path for a specific profile."""
        return self._dir_path / id

    def get_profile_info_path(self, id: str) -> Path:
        """Get the path to the profile info file."""
        return self.get_profile_dir(id) / PROFILE_INFO_FILE_NAME

    def _create_profile(self, profile: Profile):
        """
        Create a new profile.

        Args:
            profile: Profile data

        Raises:
            ValueError: If profile already exists or ID is invalid
        """
        if not profile.id.isidentifier():
            raise ValueError("Profile ID must be filesystem-safe identifier")
        if self.profile_exists(profile.id):
            raise ValueError(f"Profile ID '{profile.id}' already exists")

        profile_dir = self.get_profile_dir(profile.id)
        profile_dir.mkdir(parents=True, exist_ok=True)

        self._write_profile_info(profile.id, profile.info)

    def create_profile(
        self,
        id: str,
        *,
        name: str,
        description: Optional[str] = None,
        avatar: Optional[str] = None,
        tags: List[str] = [],
        attributes: Dict[str, Any] = {},
    ) -> Profile:
        """
        Create a new profile.

        Args:
            id: Unique filesystem-safe ID for the new profile
            **kwargs: Additional attributes for the profile

        Returns:
            Profile for the created profile

        Raises:
            ValueError: If profile already exists or ID is invalid
        """
        info = ProfileInfo(
            name=name,
            description=description,
            avatar=avatar,
            tags=tags,
            attributes=attributes,
        )
        profile = Profile(id=id, info=info)
        self._create_profile(profile)
        return profile

    def get_profile(self, id: str) -> Profile:
        """
        Get complete manifest for a specific profile.

        Args:
            id: ID of the profile to retrieve

        Returns:
            Profile containing both ID and info

        Raises:
            FileNotFoundError: If profile doesn't exist
        """
        info_path = self.get_profile_info_path(id)
        if not info_path.exists():
            raise FileNotFoundError(f"Profile '{id}' not found")

        with open(info_path, "r") as f:
            data = json.load(f)

        return Profile(id=id, info=ProfileInfo.model_validate(data))

    def update_profile_info(self, id: str, **kwargs) -> Profile:
        """
        Update information for an existing profile.

        Args:
            id: ID of the profile to update
            **kwargs: Attributes to update

        Returns:
            Updated Profile

        Raises:
            FileNotFoundError: If profile doesn't exist
        """
        profile = self.get_profile(id)
        for key, value in kwargs.items():
            setattr(profile.info, key, value)
        self._write_profile_info(id, profile.info)
        return profile

    def delete_profile(self, id: str) -> Profile:
        """
        Delete a profile.

        Args:
            id: ID of the profile to delete

        Returns:
            Profile of the deleted profile

        Raises:
            ValueError: If trying to delete default profile
            FileNotFoundError: If profile doesn't exist
        """
        if id == DEFAULT_PROFILE.id:
            raise ValueError("Cannot delete default profile")

        profile = self.get_profile(id)

        # Set default profile as active if deleting the current active profile
        if id == self.get_active_profile():
            self.set_active_profile(DEFAULT_PROFILE.id)

        shutil.rmtree(self.get_profile_dir(id))
        return profile

    def list_profiles(self) -> ProfileList:
        """
        List all available profiles.

        Returns:
            List of all Profiles
        """
        profiles = []
        for item in self._dir_path.iterdir():
            if item.is_dir():
                info_path = item / PROFILE_INFO_FILE_NAME
                if info_path.exists():
                    with open(info_path, "r") as f:
                        data = json.load(f)
                        profiles.append(
                            Profile(id=item.name, info=ProfileInfo.model_validate(data))
                        )
        return ProfileList(root=profiles)

    def set_active_profile(self, id: str) -> None:
        """
        Set the active profile.

        Args:
            id: ID of the profile to activate

        Raises:
            FileNotFoundError: If profile doesn't exist
        """
        if not self.profile_exists(id):
            raise FileNotFoundError(f"Profile '{id}' not found")

        with open(self._active_profile_file_path, "w") as f:
            f.write(f"{id}")

    def get_active_profile(self) -> str:
        """
        Get the ID of the active profile.

        Returns:
            ID of the active profile

        Raises:
            FileNotFoundError: If no active profile is set
        """
        if not self._active_profile_file_path.exists():
            self.set_active_profile(DEFAULT_PROFILE.id)
            return DEFAULT_PROFILE.id

        with open(self._active_profile_file_path, "r") as f:
            active_profile = f.readline()
            active_profile = active_profile.strip()
            return active_profile

    def _write_profile_info(self, id: str, info: ProfileInfo) -> None:
        """Internal method to write profile info to disk."""
        info_path = self.get_profile_info_path(id)
        with open(info_path, "w") as f:
            json.dump(info.model_dump(), f, indent=2)

