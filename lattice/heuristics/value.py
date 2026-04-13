"""
Value ordering heuristics determine the order in which values are tried
for a selected variable during search.

Good value ordering tries the most promising values first, leading to
solutions sooner (though it doesn't reduce worst-case complexity).
"""

from __future__ import annotations

import random
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from lattice.core import CSP


class ValueHeuristic(ABC):
    """Base class for value ordering heuristics."""

    @abstractmethod
    def order(self, csp: CSP, var_name: str, assignment: Dict[str, Any]) -> List[Any]:
        """Return the domain values for var_name in the order they should be tried."""
        ...

    @property
    def name(self) -> str:
        return self.__class__.__name__


class LeastConstrainingValue(ValueHeuristic):
    """
    Least Constraining Value (LCV) heuristic.

    Orders values by how many options they leave for neighboring variables.
    Tries the value that rules out the fewest choices for neighbors first.
    """

    def order(self, csp: CSP, var_name: str, assignment: Dict[str, Any]) -> List[Any]:
        var = csp.variables[var_name]
        if len(var.domain) <= 1:
            return list(var.domain)

        neighbors = csp.get_neighbors(var_name) - set(assignment.keys())

        def count_conflicts(value: Any) -> int:
            """Count how many neighbor-domain values become inconsistent."""
            conflicts = 0
            test_assignment = dict(assignment)
            test_assignment[var_name] = value
            for neighbor_name in neighbors:
                neighbor = csp.variables[neighbor_name]
                for n_val in neighbor.domain:
                    test_assignment[neighbor_name] = n_val
                    for constraint in csp.get_constraints_for(var_name):
                        if neighbor_name in constraint.scope:
                            if constraint.is_fully_assigned(test_assignment):
                                if not constraint.check(test_assignment):
                                    conflicts += 1
                                    break
                    del test_assignment[neighbor_name]
            return conflicts

        values = list(var.domain)
        values.sort(key=count_conflicts)
        return values


class RandomValue(ValueHeuristic):
    """Try values in random order."""

    def __init__(self, seed: Optional[int] = None):
        self._rng = random.Random(seed)

    def order(self, csp: CSP, var_name: str, assignment: Dict[str, Any]) -> List[Any]:
        values = list(csp.variables[var_name].domain)
        self._rng.shuffle(values)
        return values


class AscendingValue(ValueHeuristic):
    """Try values in ascending order."""

    def order(self, csp: CSP, var_name: str, assignment: Dict[str, Any]) -> List[Any]:
        return sorted(csp.variables[var_name].domain)


class DescendingValue(ValueHeuristic):
    """Try values in descending order."""

    def order(self, csp: CSP, var_name: str, assignment: Dict[str, Any]) -> List[Any]:
        return sorted(csp.variables[var_name].domain, reverse=True)


class MiddleOutValue(ValueHeuristic):
    """
    Try values starting from the middle of the domain, alternating outward.
    Inspired by the seed number 4515 — useful for problems where central
    values are more likely to be correct.
    """

    def order(self, csp: CSP, var_name: str, assignment: Dict[str, Any]) -> List[Any]:
        values = sorted(csp.variables[var_name].domain)
        if len(values) <= 2:
            return values
        mid = len(values) // 2
        result = [values[mid]]
        left = mid - 1
        right = mid + 1
        while left >= 0 or right < len(values):
            if right < len(values):
                result.append(values[right])
                right += 1
            if left >= 0:
                result.append(values[left])
                left -= 1
        return result
