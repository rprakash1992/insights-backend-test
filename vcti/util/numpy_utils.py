#!/usr/bin/env python

# Copyright (C) 2018 Visual Collaboration Technologies Inc.
# All Rights Reserved.
#
# This file is a property of Visual Collaboration Technologies Inc.
# Unauthorized access, reproduction or redistribution of any kind is prohibited.
"""Utility function for computing position arrays for the WTF interpreter."""

from typing import Optional

import numpy as np
from numpy.typing import NDArray


def compute_position_array(
    counts: NDArray[np.integer], dtype: Optional[np.dtype] = None
) -> NDArray[np.integer]:
    """
    Computes a position array from an array of counts.

    The function calculates cumulative sums of `counts`, which is useful for determining
    offsets in data structures such as sparse arrays or hierarchical representations.

    Args:
        counts (NDArray[np.integer]): A NumPy array representing the counts per element.
        dtype (Optional[np.dtype]): The desired data type for the output array.
                                    Defaults to the dtype of `counts` if not provided.

    Returns:
        NDArray[np.integer]: A position array where each element represents the cumulative
                             offset of the corresponding count.

    Raises:
        ValueError: If `counts` is not a 1D array.
    """
    if counts.ndim != 1:
        raise ValueError("Input `counts` must be a 1-dimensional array.")

    if dtype is None:
        dtype = counts.dtype

    pos_array = np.empty(len(counts) + 1, dtype=dtype)
    pos_array[0] = 0
    np.cumsum(counts, out=pos_array[1:])

    return pos_array


def compute_position_array_alt(
    counts: NDArray[np.integer], dtype: Optional[np.dtype] = None
) -> NDArray[np.integer]:
    """
    Optimized computation of position array using NumPy functions.

    The function calculates cumulative sums of `counts`, which is useful for determining
    offsets in data structures such as sparse arrays or hierarchical representations.

    Args:
        counts (NDArray[np.integer]): A NumPy array representing element counts.
        dtype (Optional[np.dtype]): The desired data type of the output array.
                                    Defaults to the dtype of `counts` if not provided.

    Returns:
        NDArray[np.integer]: A position array where each element represents the cumulative
                             offset of the corresponding count.

    Raises:
        ValueError: If `counts` is not a 1D array.
    """
    if counts.ndim != 1:
        raise ValueError("Input `counts` must be a 1-dimensional array.")

    if dtype is None:
        dtype = counts.dtype

    # Optimized computation
    return np.concatenate((np.array([0], dtype=dtype), np.cumsum(counts, dtype=dtype)))
