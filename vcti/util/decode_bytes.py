#!/usr/bin/env python

# Copyright (C) 2018 Visual Collaboration Technologies Inc.
# All Rights Reserved.
#
# This file is a property of Visual Collaboration Technologies Inc.
# Unauthorized access, reproduction or redistribution of any kind is prohibited.
"""Utility functions for decoding UTF-8 and other encoded byte sequences.
"""

import encodings

# Retrieve the standard UTF-8 encoding name from the Python encodings registry
UTF8_ENCODING_NAME = encodings.utf_8.getregentry().name


def decode_bytes(value: bytes, encoding: str = UTF8_ENCODING_NAME) -> str:
    """
    Decodes a byte sequence into a regular string using the specified encoding.

    Args:
        value (bytes): The byte sequence to decode.
        encoding (str, optional): The character encoding to use. Defaults to UTF-8.

    Returns:
        str: The decoded string.

    Raises:
        UnicodeDecodeError: If decoding fails due to an invalid byte sequence.
    """
    if value is None or not isinstance(value, bytes):
        raise TypeError("Expected a byte sequence")

    return value.decode(encoding)


def decode_utf8(value: bytes) -> str:
    """
    Decodes a byte sequence into a UTF-8 encoded string.

    Args:
        value (bytes): The byte sequence to decode.

    Returns:
        str: The decoded UTF-8 string.

    Raises:
        UnicodeDecodeError: If decoding fails due to an invalid byte sequence.
    """
    return decode_bytes(value)
