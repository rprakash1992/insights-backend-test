#!/usr/bin/env python

# Copyright (C) 2018 Visual Collaboration Technologies Inc.
# All Rights Reserved.
#
# This file is a property of Visual Collaboration Technologies Inc.
# Unauthorized access, reproduction or redistribution of any kind is prohibited.
"""EntityFilter: A generic filter for querying objects with id and attributes."""

from typing import Any, Generic, List, NamedTuple, Optional, Protocol, TypeVar

from vcti.util.predicate_evaluator import Modifier, evaluate


class Entity(Protocol):
    """Protocol for entities that can be filtered.

    Must have:
        - id: Unique identifier
        - attributes: Dictionary of filterable attributes
    """

    id: Any
    attributes: dict


T = TypeVar("T", bound=Entity)


class Rule(NamedTuple):
    """Specification for filtering entities based on attribute values.

    Attributes:
        attribute: Name of the attribute to filter on (e.g., "file_type")
        operator: Comparison operator (e.g., "==", "contains", ">")
        value: Value to compare the attribute against
    """

    attribute: str
    operator: str
    value: Any
    modifier: Modifier = Modifier.DEFAULT


class EntityFilter(Generic[T]):
    """Filters a collection of entities using attribute-based rules.

    Supports combining multiple rules using AND logic.
    Preserves original input order in results.

    Example:
        >>> filter = EntityFilter(files)
        >>> rules = [
        ...     Rule("size", ">", 1024),
        ...     Rule("type", "==", "pdf")
        ... ]
        >>> large_pdfs = filter.filter(rules)
    """

    def __init__(self, objects: List[T]):
        """Initialize the filter with a list of entities.

        Args:
            objects: Entities to query. Each must have:
                - id: Unique identifier
                - attributes: Dictionary of filterable attributes
        """
        self.objects = objects
        self._object_index = {obj.id: obj for obj in objects}

    def filter(self, rules: List[Rule]) -> List[T]:
        """Return all entities that match every rule.

        Args:
            rules: List of filter rules (combined using AND logic)

        Returns:
            List of entities in original order that satisfy all rules
        """
        filtered = self.objects
        for rule in rules:
            filtered = self._apply_rule(filtered, rule)
        return filtered

    def _apply_rule(self, objects: List[T], rule: Rule) -> List[T]:
        """Apply a single rule to a list of entities.

        Args:
            objects: List of entities to filter
            rule: A rule to apply

        Returns:
            Entities that match the rule
        """
        return [
            obj
            for obj in objects
            if evaluate(
                lhs=obj.attributes.get(rule.attribute),
                op=rule.operator,
                rhs=rule.value,
                modifier=rule.modifier,
            )
        ]

    def matching_ids(self, rules: List[Rule]) -> List[Any]:
        """Return IDs of entities that match all given rules.

        Args:
            rules: List of filter rules

        Returns:
            IDs of matching entities in original order
        """
        return [obj.id for obj in self.filter(rules)]

    def first_match(self, rules: List[Rule]) -> Optional[T]:
        """Return the first matching entity or None.

        Args:
            rules: List of filter rules

        Returns:
            First matching entity, or None if no match is found
        """
        matches = self.filter(rules)
        return matches[0] if matches else None

    def first_match_id(self, rules: List[Rule]) -> Optional[Any]:
        """Return the ID of the first matching entity or None.

        Args:
            rules: List of filter rules

        Returns:
            ID of the first matching entity, or None if no match is found
        """
        match = self.first_match(rules)
        return match.id if match else None

    def get_object(self, id: Any) -> Optional[T]:
        """Return the entity with the specified ID.

        Args:
            id: Unique identifier of the entity

        Returns:
            Entity with the given ID, or None if not found
        """
        return self._object_index.get(id)
