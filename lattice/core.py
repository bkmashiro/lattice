"""
Core CSP data structures: Variable, Domain, Constraint, and CSP.

A CSP is defined by:
- A set of variables, each with a domain of possible values
- A set of constraints that restrict which combinations of values are allowed
- An optional objective function for optimization problems
"""

from __future__ import annotations

import copy
import itertools
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import (
    Any,
    Callable,
    Dict,
    FrozenSet,
    Iterable,
    List,
    Optional,
    Protocol,
    Set,
    Tuple,
    Union,
)


class ConstraintType(Enum):
    """Classification of constraint types for solver optimization."""
    UNARY = auto()
    BINARY = auto()
    NARY = auto()
    GLOBAL = auto()


class Domain:
    """
    Represents the set of possible values for a variable.

    Supports efficient operations: removal, restoration (for backtracking),
    membership testing, and iteration. Maintains a history stack for
    checkpoint/restore during search.
    """

    def __init__(self, values: Iterable[Any]):
        self._values: Set[Any] = set(values)
        self._initial: FrozenSet[Any] = frozenset(self._values)
        self._history: List[Set[Any]] = []
        self._removed_log: List[List[Tuple[Any, str]]] = []

    @property
    def values(self) -> Set[Any]:
        return self._values

    @property
    def initial_values(self) -> FrozenSet[Any]:
        return self._initial

    def __len__(self) -> int:
        return len(self._values)

    def __contains__(self, value: Any) -> bool:
        return value in self._values

    def __iter__(self):
        return iter(sorted(self._values) if all(isinstance(v, (int, float, str)) for v in self._values) else iter(self._values))

    def __repr__(self) -> str:
        return f"Domain({sorted(self._values) if len(self._values) <= 10 else f'|{len(self._values)}|'})"

    def is_empty(self) -> bool:
        return len(self._values) == 0

    def is_singleton(self) -> bool:
        return len(self._values) == 1

    def get_single(self) -> Any:
        """Return the single remaining value. Raises if domain is not singleton."""
        if not self.is_singleton():
            raise ValueError(f"Domain has {len(self._values)} values, not 1")
        return next(iter(self._values))

    def remove(self, value: Any, reason: str = "") -> bool:
        """Remove a value from the domain. Returns True if value was present."""
        if value in self._values:
            self._values.discard(value)
            if self._removed_log:
                self._removed_log[-1].append((value, reason))
            return True
        return False

    def restrict_to(self, values: Set[Any], reason: str = "") -> Set[Any]:
        """Restrict domain to intersection with given values. Returns removed values."""
        removed = self._values - values
        for v in removed:
            self.remove(v, reason)
        return removed

    def save(self) -> None:
        """Save current state for backtracking."""
        self._history.append(set(self._values))
        self._removed_log.append([])

    def restore(self) -> List[Tuple[Any, str]]:
        """Restore to last saved state. Returns log of removals since save."""
        if self._history:
            self._values = self._history.pop()
            return self._removed_log.pop()
        return []

    def copy(self) -> Domain:
        """Create a deep copy of this domain."""
        d = Domain(self._values)
        d._initial = self._initial
        return d

    @property
    def reduction_ratio(self) -> float:
        """How much the domain has been reduced from its initial size."""
        if len(self._initial) == 0:
            return 0.0
        return 1.0 - len(self._values) / len(self._initial)


class Variable:
    """
    A CSP variable with a name, domain, and optional metadata.
    """

    def __init__(self, name: str, domain: Union[Domain, Iterable[Any]], **metadata):
        self.name = name
        self.domain = domain if isinstance(domain, Domain) else Domain(domain)
        self.metadata = metadata
        self._assigned: Optional[Any] = None

    @property
    def is_assigned(self) -> bool:
        return self._assigned is not None

    @property
    def value(self) -> Optional[Any]:
        return self._assigned

    def assign(self, value: Any) -> None:
        if value not in self.domain:
            raise ValueError(f"Cannot assign {value} to {self.name}: not in domain {self.domain}")
        self._assigned = value

    def unassign(self) -> None:
        self._assigned = None

    def __repr__(self) -> str:
        if self.is_assigned:
            return f"Var({self.name}={self._assigned})"
        return f"Var({self.name}, {self.domain})"

    def __hash__(self) -> int:
        return hash(self.name)

    def __eq__(self, other) -> bool:
        if isinstance(other, Variable):
            return self.name == other.name
        return NotImplemented


class Constraint:
    """
    A constraint over one or more variables.

    The constraint is defined by:
    - A scope: the variables it involves
    - A check function: returns True if an assignment satisfies the constraint
    - Optional metadata (name, type classification, etc.)
    """

    def __init__(
        self,
        scope: List[str],
        check: Callable[..., bool],
        name: str = "",
        constraint_type: Optional[ConstraintType] = None,
    ):
        self.scope = scope
        self._check = check
        self.name = name or f"C({','.join(scope)})"
        self.type = constraint_type or self._infer_type()
        self._propagator: Optional[Callable] = None

    def _infer_type(self) -> ConstraintType:
        n = len(self.scope)
        if n == 1:
            return ConstraintType.UNARY
        elif n == 2:
            return ConstraintType.BINARY
        else:
            return ConstraintType.NARY

    def check(self, assignment: Dict[str, Any]) -> bool:
        """Check if the constraint is satisfied by the given assignment."""
        values = []
        for var_name in self.scope:
            if var_name not in assignment:
                return True  # Constraint not yet applicable
            values.append(assignment[var_name])
        return self._check(*values)

    def is_fully_assigned(self, assignment: Dict[str, Any]) -> bool:
        """Check if all variables in scope have assignments."""
        return all(v in assignment for v in self.scope)

    def set_propagator(self, propagator: Callable) -> None:
        """Set a custom propagation function for this constraint."""
        self._propagator = propagator

    @property
    def propagator(self) -> Optional[Callable]:
        return self._propagator

    def __repr__(self) -> str:
        return f"Constraint({self.name})"

    def __hash__(self) -> int:
        return hash((self.name, tuple(self.scope)))


# --- Common constraint factories ---

def all_different(*var_names: str, name: str = "") -> Constraint:
    """All variables must have different values (single n-ary constraint)."""
    scope = list(var_names)
    def check(*values):
        return len(set(values)) == len(values)
    return Constraint(scope, check, name=name or f"AllDiff({','.join(scope)})",
                      constraint_type=ConstraintType.GLOBAL)


def all_different_pairwise(*var_names: str, name: str = "") -> List[Constraint]:
    """Decompose all-different into pairwise not-equal constraints (better for AC-3/MAC)."""
    constraints = []
    scope = list(var_names)
    prefix = name or "AllDiff"
    for i in range(len(scope)):
        for j in range(i + 1, len(scope)):
            constraints.append(not_equal(scope[i], scope[j],
                                         name=f"{prefix}({scope[i]},{scope[j]})"))
    return constraints


def all_equal(*var_names: str, name: str = "") -> Constraint:
    """All variables must have the same value."""
    scope = list(var_names)
    def check(*values):
        return len(set(values)) == 1
    return Constraint(scope, check, name=name or f"AllEqual({','.join(scope)})",
                      constraint_type=ConstraintType.GLOBAL)


def sum_equals(var_names: List[str], target: int, name: str = "") -> Constraint:
    """Sum of variables must equal target."""
    def check(*values):
        return sum(values) == target
    return Constraint(var_names, check, name=name or f"Sum={target}",
                      constraint_type=ConstraintType.GLOBAL)


def sum_at_most(var_names: List[str], target: int, name: str = "") -> Constraint:
    """Sum of variables must be at most target."""
    def check(*values):
        return sum(values) <= target
    return Constraint(var_names, check, name=name or f"Sum<={target}",
                      constraint_type=ConstraintType.GLOBAL)


def product_equals(var_names: List[str], target: int, name: str = "") -> Constraint:
    """Product of variables must equal target."""
    def check(*values):
        result = 1
        for v in values:
            result *= v
        return result == target
    return Constraint(var_names, check, name=name or f"Prod={target}",
                      constraint_type=ConstraintType.GLOBAL)


def not_equal(var1: str, var2: str, name: str = "") -> Constraint:
    """Two variables must not be equal."""
    return Constraint([var1, var2], lambda a, b: a != b,
                      name=name or f"{var1}!={var2}", constraint_type=ConstraintType.BINARY)


def less_than(var1: str, var2: str, name: str = "") -> Constraint:
    """var1 must be less than var2."""
    return Constraint([var1, var2], lambda a, b: a < b,
                      name=name or f"{var1}<{var2}", constraint_type=ConstraintType.BINARY)


def greater_than(var1: str, var2: str, name: str = "") -> Constraint:
    """var1 must be greater than var2."""
    return Constraint([var1, var2], lambda a, b: a > b,
                      name=name or f"{var1}>{var2}", constraint_type=ConstraintType.BINARY)


def abs_diff_equals(var1: str, var2: str, diff: int, name: str = "") -> Constraint:
    """Absolute difference between two variables must equal diff."""
    return Constraint([var1, var2], lambda a, b: abs(a - b) == diff,
                      name=name or f"|{var1}-{var2}|={diff}", constraint_type=ConstraintType.BINARY)


def implies(var1: str, val1: Any, var2: str, val2: Any, name: str = "") -> Constraint:
    """If var1 == val1, then var2 must == val2."""
    return Constraint([var1, var2], lambda a, b: a != val1 or b == val2,
                      name=name or f"{var1}={val1}=>{var2}={val2}", constraint_type=ConstraintType.BINARY)


class CSP:
    """
    A Constraint Satisfaction Problem.

    Holds variables, constraints, and provides methods for:
    - Adding variables and constraints
    - Querying the constraint graph
    - Computing statistics
    """

    def __init__(self, name: str = "CSP"):
        self.name = name
        self._variables: Dict[str, Variable] = {}
        self._constraints: List[Constraint] = []
        self._var_constraints: Dict[str, List[Constraint]] = {}
        self._neighbors: Dict[str, Set[str]] = {}

    @property
    def variables(self) -> Dict[str, Variable]:
        return self._variables

    @property
    def constraints(self) -> List[Constraint]:
        return self._constraints

    def add_variable(self, var: Variable) -> None:
        """Add a variable to the CSP."""
        if var.name in self._variables:
            raise ValueError(f"Variable {var.name} already exists")
        self._variables[var.name] = var
        self._var_constraints[var.name] = []
        self._neighbors[var.name] = set()

    def add_variables(self, *variables: Variable) -> None:
        """Add multiple variables."""
        for v in variables:
            self.add_variable(v)

    def add_constraint(self, constraint: Constraint) -> None:
        """Add a constraint to the CSP."""
        for var_name in constraint.scope:
            if var_name not in self._variables:
                raise ValueError(f"Variable {var_name} not found in CSP")
        self._constraints.append(constraint)
        for var_name in constraint.scope:
            self._var_constraints[var_name].append(constraint)
            for other in constraint.scope:
                if other != var_name:
                    self._neighbors[var_name].add(other)

    def add_constraints(self, *constraints: Constraint) -> None:
        """Add multiple constraints."""
        for c in constraints:
            self.add_constraint(c)

    def get_constraints_for(self, var_name: str) -> List[Constraint]:
        """Get all constraints involving a variable."""
        return self._var_constraints.get(var_name, [])

    def get_binary_constraints(self, var1: str, var2: str) -> List[Constraint]:
        """Get constraints involving exactly var1 and var2."""
        result = []
        for c in self._var_constraints.get(var1, []):
            if var2 in c.scope and len(c.scope) == 2:
                result.append(c)
        return result

    def get_neighbors(self, var_name: str) -> Set[str]:
        """Get all variables that share a constraint with var_name."""
        return self._neighbors.get(var_name, set())

    def is_consistent(self, assignment: Dict[str, Any]) -> bool:
        """Check if an assignment is consistent with all constraints."""
        for constraint in self._constraints:
            if constraint.is_fully_assigned(assignment):
                if not constraint.check(assignment):
                    return False
        return True

    def is_complete(self, assignment: Dict[str, Any]) -> bool:
        """Check if assignment covers all variables."""
        return all(v in assignment for v in self._variables)

    def is_solution(self, assignment: Dict[str, Any]) -> bool:
        """Check if assignment is a complete, consistent solution."""
        return self.is_complete(assignment) and self.is_consistent(assignment)

    def unassigned_variables(self, assignment: Dict[str, Any]) -> List[str]:
        """Return names of variables not yet assigned."""
        return [v for v in self._variables if v not in assignment]

    @property
    def num_variables(self) -> int:
        return len(self._variables)

    @property
    def num_constraints(self) -> int:
        return len(self._constraints)

    @property
    def constraint_density(self) -> float:
        """Ratio of actual constraints to maximum possible binary constraints."""
        n = self.num_variables
        if n < 2:
            return 0.0
        max_binary = n * (n - 1) / 2
        return self.num_constraints / max_binary

    @property
    def domain_sizes(self) -> Dict[str, int]:
        """Map of variable names to their current domain sizes."""
        return {name: len(var.domain) for name, var in self._variables.items()}

    @property
    def total_search_space(self) -> int:
        """Product of all domain sizes (without constraint propagation)."""
        result = 1
        for var in self._variables.values():
            result *= len(var.domain)
        return result

    def summary(self) -> str:
        """Return a human-readable summary of the CSP."""
        lines = [
            f"CSP: {self.name}",
            f"  Variables: {self.num_variables}",
            f"  Constraints: {self.num_constraints}",
            f"  Constraint density: {self.constraint_density:.3f}",
            f"  Search space: {self.total_search_space:.2e}",
        ]
        return "\n".join(lines)

    def copy(self) -> CSP:
        """Create a deep copy of this CSP."""
        new_csp = CSP(self.name)
        for name, var in self._variables.items():
            new_var = Variable(name, var.domain.copy(), **var.metadata)
            new_csp.add_variable(new_var)
        for c in self._constraints:
            new_csp.add_constraint(c)
        return new_csp

    def __repr__(self) -> str:
        return f"CSP({self.name}: {self.num_variables} vars, {self.num_constraints} constraints)"
