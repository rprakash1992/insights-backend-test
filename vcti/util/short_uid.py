#!/usr/bin/env python

# Copyright (C) 2018 Visual Collaboration Technologies Inc.
# All Rights Reserved.
#
# This file is a property of Visual Collaboration Technologies Inc.
# Unauthorized access, reproduction or redistribution of any kind is prohibited.
"""Short UID generator for used to generate consice unique identifiers."""

import base64
import hashlib
import random
import time
from typing import Optional


class ShortUID:
    """
    Generate short, reasonably unique IDs typically used as a part of
    unique file or directory names.
    """

    def __init__(self, entropy: Optional[str] = None, length: int = 8):
        """
        Initialize the generator.

        Args:
            entropy (Optional[str]): Optional base entropy seed.
            length (int): Number of characters in the generated ID (default: 8).
        """
        self.entropy = entropy
        self.length = length

    def generate(self, salt: Optional[str] = None) -> str:
        """
        Generate a short, unique identifier.

        Args:
            salt (Optional[str]): Additional salt or context string (e.g., filename).

        Returns:
            str: A short unique ID.
        """
        base = f"{self.entropy or ''}-{salt or ''}-{time.time_ns()}-{random.random()}"
        digest = hashlib.sha256(base.encode()).digest()
        encoded = base64.urlsafe_b64encode(digest).decode("utf-8")
        return encoded.rstrip("=\n")[: self.length]

    @classmethod
    def quick(cls, length: int = 8) -> str:
        """Convenience method to quickly generate a short ID."""
        return cls(length=length).generate()
