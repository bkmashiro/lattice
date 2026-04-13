"""
Variable ordering heuristics determine which variable to assign next during search.

Good variable ordering can dramatically reduce search time by failing early
on heavily constrained variables.
"""

from __future__ import annotations

import random
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from lattice.core import CSP


class VariableHeuristic(ABC):
    """Base class for variable selection heuristics."""

    @abstractmethod
    def select(self, csp: CSP, assignment: Dict[str, Any]) -> str:
        """Select the next variable to assign. Returns variable name."""
        ...

    @property
    def name(self) -> str:
        return self.__class__.__name__


class MRV(VariableHeuristic):
    """
    Minimum Remaining Values (MRV) heuristic.

    Also known as "fail-first" — selects the variable with the fewest
    remaining legal values. This tends to detect failures earlier, pruning
    the search tree.
    """

    def select(self, csp: CSP, assignment: Dict[str, Any]) -> str:
        unassigned = csp.unassigned_variables(assignment)
        if not unassigned:
            raise ValueError("No unassigned variables")
        return min(unassigned, key=lambda v: len(csp.variables[v].domain))


class DegreeHeuristic(VariableHeuristic):
    """
    Degree heuristic: select the variable involved in the most
    constraints with other unassigned variables.
    """

    def select(self, csp: CSP, assignment: Dict[str, Any]) -> str:
        unassigned = csp.unassigned_variables(assignment)
        if not unassigned:
            raise ValueError("No unassigned variables")
        unassigned_set = set(unassigned)

        def degree(var_name: str) -> int:
            return len(csp.get_neighbors(var_name) & unassigned_set)

        return max(unassigned, key=degree)


class MRVWithTiebreaker(VariableHeuristic):
    """
    MRV with degree heuristic as tiebreaker.

    When multiple variables have the same minimum remaining values,
    break ties by choosing the one with the highest degree.
    """

    def select(self, csp: CSP, assignment: Dict[str, Any]) -> str:
        unassigned = csp.unassigned_variables(assignment)
        if not unassigned:
            raise ValueError("No unassigned variables")
        unassigned_set = set(unassigned)

        def key(var_name: str):
            domain_size = len(csp.variables[var_name].domain)
            degree = len(csp.get_neighbors(var_name) & unassigned_set)
            # Sort by domain size ascending, then degree descending
            return (domain_size, -degree)

        return min(unassigned, key=key)


class MaxDomainHeuristic(VariableHeuristic):
    """
    Select the variable with the largest remaining domain.
    Opposite of MRV — sometimes useful for specific problem structures.
    """

    def select(self, csp: CSP, assignment: Dict[str, Any]) -> str:
        unassigned = csp.unassigned_variables(assignment)
        if not unassigned:
            raise ValueError("No unassigned variables")
        return max(unassigned, key=lambda v: len(csp.variables[v].domain))


class RandomVariable(VariableHeuristic):
    """Select a random unassigned variable. Useful as a baseline."""

    def __init__(self, seed: Optional[int] = None):
        self._rng = random.Random(seed)

    def select(self, csp: CSP, assignment: Dict[str, Any]) -> str:
        unassigned = csp.unassigned_variables(assignment)
        if not unassigned:
            raise ValueError("No unassigned variables")
        return self._rng.choice(unassigned)


class FirstUnassigned(VariableHeuristic):
    """Select the first unassigned variable in order. Simplest possible heuristic."""

    def select(self, csp: CSP, assignment: Dict[str, Any]) -> str:
        unassigned = csp.unassigned_variables(assignment)
        if not unassigned:
            raise ValueError("No unassigned variables")
        return unassigned[0]
