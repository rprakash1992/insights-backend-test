#!/usr/bin/env python

# Copyright (C) 2018 Visual Collaboration Technologies Inc.
# All Rights Reserved.
#
# This file is a property of Visual Collaboration Technologies Inc.
# Unauthorized access, reproduction or redistribution of any kind is prohibited.
"""A flexible predicate evaluator supporting common operators with case sensitivity modifiers."""

import re
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any, Dict, Literal

from vcti.util.value_generated_enums import EnumValueLowerCase, auto_enum_value


class Modifier(EnumValueLowerCase):
    """Modifiers that alter comparison behavior."""

    DEFAULT = auto_enum_value()  # Default behavior (case-insensitive for strings)
    IGNORE_CASE = "ignore_case"  # Case-insensitive comparison
    CASE_SENSITIVE = "case_sensitive"  # Case-sensitive comparison


OperatorFunc = Callable[[Any, Any, Modifier], bool]
OperatorsDict = Mapping[str, OperatorFunc]


def _normalize_value(value: Any, modifier: Modifier = Modifier.DEFAULT) -> Any:
    """Normalize string/path values based on case sensitivity modifier.

    Args:
        value: Input value to normalize
        modifier: Modifier flag controlling normalization

    Returns:
        Normalized value (lowercased strings unless CASE_SENSITIVE flag is set)
    """
    if isinstance(value, (str, Path)):
        if modifier == Modifier.CASE_SENSITIVE:
            return str(value)
        return str(value).lower()
    elif isinstance(value, list):
        return [_normalize_value(item, modifier) for item in value]
    else:
        return value


# Core operator implementations
OP_NUMERIC: OperatorsDict = {
    "<": lambda x, y, _: x < y,
    "<=": lambda x, y, _: x <= y,
    "==": lambda x, y, _: x == y,
    "!=": lambda x, y, _: x != y,
    ">=": lambda x, y, _: x >= y,
    ">": lambda x, y, _: x > y,
}

OP_COLLECTION: OperatorsDict = {
    "in": lambda x, y, _: x in y if hasattr(y, "__contains__") else False,
    "!in": lambda x, y, _: x not in y if hasattr(y, "__contains__") else False,
    "contains": lambda x, y, _: y in x if hasattr(x, "__contains__") else False,
    "!contains": lambda x, y, _: y not in x if hasattr(x, "__contains__") else False,
    "all": lambda x, y, _: (
        all(item in y for item in x) if hasattr(x, "__iter__") else False
    ),
    "any": lambda x, y, _: (
        any(item in y for item in x) if hasattr(x, "__iter__") else False
    ),
}

OP_STRING: OperatorsDict = {
    "startswith": lambda x, y, modifier: x.startswith(y),
    "endswith": lambda x, y, modifier: x.endswith(y),
}

OP_REGEX: OperatorsDict = {
    "matches": lambda x, y, modifier: bool(
        re.search(
            str(y),
            str(x),
            0 if modifier == Modifier.CASE_SENSITIVE else re.IGNORECASE,
        )
    )
}

# Combine all core operators
CANONICAL_OPERATORS: OperatorsDict = {
    **OP_NUMERIC,
    **OP_COLLECTION,
    **OP_STRING,
    **OP_REGEX,
}

# Operator aliases for backward compatibility and convenience
OPERATOR_ALIASES: Dict[str, str] = {
    "lt": "<",
    "le": "<=",
    "eq": "==",
    "ne": "!=",
    "ge": ">=",
    "gt": ">",
    "has": "contains",
    "!has": "!contains",
}


def _build_operator_registry() -> OperatorsDict:
    """Build the complete operator registry including aliases.

    Returns:
        Complete operator dictionary mapping all names to implementations

    Raises:
        ValueError: If any alias points to an unknown operator
    """
    registry = dict(CANONICAL_OPERATORS)
    for alias, canonical in OPERATOR_ALIASES.items():
        if canonical not in registry:
            raise ValueError(
                f"Alias '{alias}' points to unknown operator '{canonical}'"
            )
        registry[alias] = registry[canonical]
    return registry


OPERATORS = _build_operator_registry()


def evaluate(
    lhs: Any, op: str, rhs: Any, modifier: Modifier = Modifier.DEFAULT
) -> bool:
    """Evaluate a condition between two values using the specified operator.

    Args:
        lhs: Left-hand side value for comparison
        op: Name of the operator (e.g., '==', 'contains')
        rhs: Right-hand side value for comparison
        modifier: Optional set of Modifier flags to control comparison behavior

    Returns:
        bool: True if the condition is satisfied, False otherwise

    Raises:
        ValueError: If the operator name is not recognized

    Examples:
        >>> evaluate("hello", "eq", "HELLO")  # Case-insensitive by default
        True
        >>> evaluate([1, 2], "contains", 2)
        True
        >>> evaluate("text", "matches", r"T.XT", Modifier.IGNORE_CASE)
        True
    """
    if op not in OPERATORS:
        raise ValueError(
            f"Unsupported operator: {op}. Valid operators: {sorted(OPERATORS.keys())}"
        )

    try:
        normalized_lhs = _normalize_value(lhs, modifier)
        normalized_rhs = _normalize_value(rhs, modifier)
        return OPERATORS[op](normalized_lhs, normalized_rhs, modifier)
    except (TypeError, ValueError, re.error):
        raise


OperatorLiteral = Literal[*OPERATORS.keys()]
EQ_OP = "eq"

if __name__ == "__main__":
    mods_ic = Modifier.IGNORE_CASE
    mods_cs = Modifier.CASE_SENSITIVE

    print(evaluate("hello", "eq", "HELLO"))  # True (default is case-insensitive)
    print(evaluate("hello", "eq", "HELLO", mods_ic))  # True
    print(evaluate("hello", "eq", "HELLO", mods_cs))  # False
    print(evaluate("hello world", "matches", r"HELLO", mods_ic))  # True
    print(evaluate("hello world", "matches", r"HELLO", mods_cs))  # False
    print(evaluate("example", "contains", "AMP", mods_ic))  # True
    print(evaluate("example", "contains", "AMP", mods_cs))  # False
    print(evaluate(2, "in", [1, 2, 3]))  # True
