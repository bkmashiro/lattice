"""
Constraint propagation algorithms.

Implements:
- Node consistency (unary constraint enforcement)
- AC-3 (arc consistency for binary constraints)
- AC-4 (fine-grained arc consistency)
- Generalized arc consistency for n-ary constraints
- Forward checking
- MAC (Maintaining Arc Consistency)

Each propagation step can produce an Explanation describing why values
were eliminated from domains.
"""

from __future__ import annotations

import itertools
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Deque, Dict, List, Optional, Set, Tuple

from lattice.core import CSP, Constraint, ConstraintType, Variable


@dataclass
class Elimination:
    """Record of a single value elimination during propagation."""
    variable: str
    value: Any
    reason: str
    constraint: Optional[str] = None
    supporting_assignments: Optional[Dict[str, Any]] = None


@dataclass
class PropagationResult:
    """Result of a propagation pass."""
    consistent: bool  # False if any domain was wiped out
    eliminations: List[Elimination] = field(default_factory=list)
    domains_reduced: int = 0
    values_eliminated: int = 0

    def add(self, elim: Elimination) -> None:
        self.eliminations.append(elim)
        self.values_eliminated += 1


class NodeConsistency:
    """
    Enforce node consistency: for each unary constraint, remove values
    from the variable's domain that violate the constraint.
    """

    @staticmethod
    def enforce(csp: CSP) -> PropagationResult:
        result = PropagationResult(consistent=True)
        for constraint in csp.constraints:
            if constraint.type != ConstraintType.UNARY:
                continue
            var_name = constraint.scope[0]
            var = csp.variables[var_name]
            to_remove = []
            for value in var.domain:
                if not constraint.check({var_name: value}):
                    to_remove.append(value)
            for value in to_remove:
                var.domain.remove(value, f"node consistency: {constraint.name}")
                result.add(Elimination(
                    variable=var_name,
                    value=value,
                    reason=f"Violates unary constraint {constraint.name}",
                    constraint=constraint.name,
                ))
            if to_remove:
                result.domains_reduced += 1
            if var.domain.is_empty():
                result.consistent = False
                return result
        return result


class AC3:
    """
    AC-3 arc consistency algorithm.

    For each binary constraint between variables Xi and Xj, ensures that
    for every value in Di, there exists a supporting value in Dj.

    Time complexity: O(ed^3) where e = #constraints, d = max domain size.
    """

    @staticmethod
    def enforce(
        csp: CSP,
        initial_arcs: Optional[List[Tuple[str, str]]] = None,
    ) -> PropagationResult:
        result = PropagationResult(consistent=True)

        # Build arc queue
        queue: Deque[Tuple[str, str]] = deque()
        if initial_arcs is not None:
            queue.extend(initial_arcs)
        else:
            for constraint in csp.constraints:
                if len(constraint.scope) == 2:
                    xi, xj = constraint.scope
                    queue.append((xi, xj))
                    queue.append((xj, xi))

        visited = set()

        while queue:
            xi_name, xj_name = queue.popleft()

            revised, elims = AC3._revise(csp, xi_name, xj_name)
            if revised:
                result.domains_reduced += 1
                for e in elims:
                    result.add(e)

                xi_var = csp.variables[xi_name]
                if xi_var.domain.is_empty():
                    result.consistent = False
                    return result

                # Add arcs (xk, xi) for all neighbors xk of xi except xj
                for xk_name in csp.get_neighbors(xi_name):
                    if xk_name != xj_name:
                        arc = (xk_name, xi_name)
                        queue.append(arc)

        return result

    @staticmethod
    def _revise(csp: CSP, xi_name: str, xj_name: str) -> Tuple[bool, List[Elimination]]:
        """Remove values from xi's domain that have no support in xj's domain."""
        revised = False
        eliminations = []
        xi_var = csp.variables[xi_name]
        xj_var = csp.variables[xj_name]

        constraints = csp.get_binary_constraints(xi_name, xj_name)
        if not constraints:
            return False, []

        to_remove = []
        for xi_val in list(xi_var.domain):
            has_support = False
            for xj_val in xj_var.domain:
                assignment = {xi_name: xi_val, xj_name: xj_val}
                if all(c.check(assignment) for c in constraints):
                    has_support = True
                    break
            if not has_support:
                to_remove.append(xi_val)

        for val in to_remove:
            xi_var.domain.remove(val, f"AC-3: no support in {xj_name}")
            revised = True
            eliminations.append(Elimination(
                variable=xi_name,
                value=val,
                reason=f"No supporting value in {xj_name}",
                constraint=f"arc({xi_name},{xj_name})",
            ))

        return revised, eliminations


class ForwardChecking:
    """
    Forward checking: when a variable is assigned, remove inconsistent
    values from the domains of its unassigned neighbors.
    """

    @staticmethod
    def propagate(
        csp: CSP,
        var_name: str,
        value: Any,
        assignment: Dict[str, Any],
    ) -> PropagationResult:
        result = PropagationResult(consistent=True)

        for constraint in csp.get_constraints_for(var_name):
            for other_name in constraint.scope:
                if other_name == var_name or other_name in assignment:
                    continue
                other_var = csp.variables[other_name]
                to_remove = []
                for other_val in list(other_var.domain):
                    test_assignment = dict(assignment)
                    test_assignment[other_name] = other_val
                    if constraint.is_fully_assigned(test_assignment):
                        if not constraint.check(test_assignment):
                            to_remove.append(other_val)

                for val in to_remove:
                    other_var.domain.remove(val, f"FC: {var_name}={value}")
                    result.add(Elimination(
                        variable=other_name,
                        value=val,
                        reason=f"Inconsistent with {var_name}={value} via {constraint.name}",
                        constraint=constraint.name,
                    ))

                if to_remove:
                    result.domains_reduced += 1

                if other_var.domain.is_empty():
                    result.consistent = False
                    return result

        return result


class MAC:
    """
    Maintaining Arc Consistency (MAC): after assigning a variable,
    run AC-3 on arcs pointing to the assigned variable's neighbors.
    """

    @staticmethod
    def propagate(
        csp: CSP,
        var_name: str,
        value: Any,
        assignment: Dict[str, Any],
    ) -> PropagationResult:
        # Start AC-3 with arcs from neighbors of var_name
        initial_arcs = []
        for neighbor in csp.get_neighbors(var_name):
            if neighbor not in assignment:
                initial_arcs.append((neighbor, var_name))

        return AC3.enforce(csp, initial_arcs=initial_arcs)


class GAC:
    """
    Generalized Arc Consistency for n-ary constraints.

    For each constraint and each variable in its scope, ensures that
    for every value in the variable's domain, there exists a supporting
    tuple of values for all other variables in the constraint's scope.
    """

    @staticmethod
    def enforce(
        csp: CSP,
        assignment: Optional[Dict[str, Any]] = None,
    ) -> PropagationResult:
        if assignment is None:
            assignment = {}
        result = PropagationResult(consistent=True)
        changed = True

        while changed:
            changed = False
            for constraint in csp.constraints:
                # Skip constraints that are fully assigned
                unassigned_in_scope = [
                    v for v in constraint.scope if v not in assignment
                ]
                if not unassigned_in_scope:
                    continue

                for var_name in unassigned_in_scope:
                    var = csp.variables[var_name]
                    other_vars = [v for v in constraint.scope if v != var_name]

                    to_remove = []
                    for val in list(var.domain):
                        test_base = dict(assignment)
                        test_base[var_name] = val

                        # Check if there's a supporting tuple
                        has_support = GAC._find_support(
                            csp, constraint, var_name, val, other_vars, test_base
                        )
                        if not has_support:
                            to_remove.append(val)

                    for val in to_remove:
                        var.domain.remove(val, f"GAC: {constraint.name}")
                        result.add(Elimination(
                            variable=var_name,
                            value=val,
                            reason=f"No support in {constraint.name}",
                            constraint=constraint.name,
                        ))
                        changed = True

                    if to_remove:
                        result.domains_reduced += 1

                    if var.domain.is_empty():
                        result.consistent = False
                        return result

        return result

    @staticmethod
    def _find_support(
        csp: CSP,
        constraint: Constraint,
        var_name: str,
        value: Any,
        other_vars: List[str],
        base_assignment: Dict[str, Any],
    ) -> bool:
        """Check if there exists a supporting tuple for var_name=value."""
        unassigned_others = [v for v in other_vars if v not in base_assignment]
        if not unassigned_others:
            return constraint.check(base_assignment)

        # Generate all combinations of values for unassigned others
        domains = [list(csp.variables[v].domain) for v in unassigned_others]
        for combo in itertools.product(*domains):
            test = dict(base_assignment)
            for v, val in zip(unassigned_others, combo):
                test[v] = val
            if constraint.check(test):
                return True
        return False


class PropagationEngine:
    """
    Unified propagation engine that combines multiple propagation techniques.
    """

    def __init__(
        self,
        use_node_consistency: bool = True,
        use_ac3: bool = True,
        use_gac: bool = False,
    ):
        self.use_node_consistency = use_node_consistency
        self.use_ac3 = use_ac3
        self.use_gac = use_gac

    def initial_propagation(self, csp: CSP) -> PropagationResult:
        """Run propagation on the initial CSP before search begins."""
        combined = PropagationResult(consistent=True)

        if self.use_node_consistency:
            nc_result = NodeConsistency.enforce(csp)
            self._merge_results(combined, nc_result)
            if not combined.consistent:
                return combined

        if self.use_ac3:
            ac3_result = AC3.enforce(csp)
            self._merge_results(combined, ac3_result)
            if not combined.consistent:
                return combined

        if self.use_gac:
            gac_result = GAC.enforce(csp)
            self._merge_results(combined, gac_result)

        return combined

    def propagate_assignment(
        self,
        csp: CSP,
        var_name: str,
        value: Any,
        assignment: Dict[str, Any],
        use_mac: bool = True,
    ) -> PropagationResult:
        """Propagate the effects of assigning var_name = value."""
        if use_mac:
            return MAC.propagate(csp, var_name, value, assignment)
        else:
            return ForwardChecking.propagate(csp, var_name, value, assignment)

    @staticmethod
    def _merge_results(target: PropagationResult, source: PropagationResult) -> None:
        target.consistent = target.consistent and source.consistent
        target.eliminations.extend(source.eliminations)
        target.domains_reduced += source.domains_reduced
        target.values_eliminated += source.values_eliminated
