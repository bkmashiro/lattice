"""
The main CSP solver engine.

Implements backtracking search with:
- Configurable propagation (forward checking, MAC, GAC)
- Variable and value ordering heuristics
- Backjumping (conflict-directed backtracking)
- Symmetry breaking
- Solution counting and enumeration
- Search statistics and explanation trails
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from lattice.core import CSP, Variable
from lattice.heuristics import (
    AscendingValue,
    MRVWithTiebreaker,
    ValueHeuristic,
    VariableHeuristic,
)
from lattice.propagation import (
    AC3,
    ForwardChecking,
    GAC,
    MAC,
    NodeConsistency,
    PropagationEngine,
    PropagationResult,
    Elimination,
)


class PropagationLevel(Enum):
    NONE = auto()
    FORWARD_CHECKING = auto()
    MAC = auto()
    GAC = auto()


@dataclass
class SolverConfig:
    """Configuration for the CSP solver."""
    propagation: PropagationLevel = PropagationLevel.MAC
    variable_heuristic: Optional[VariableHeuristic] = None
    value_heuristic: Optional[ValueHeuristic] = None
    use_backjumping: bool = False
    max_solutions: int = 1  # 0 = find all
    time_limit: float = 60.0  # seconds
    node_limit: int = 0  # 0 = unlimited
    track_explanations: bool = False
    initial_propagation: bool = True

    def __post_init__(self):
        if self.variable_heuristic is None:
            self.variable_heuristic = MRVWithTiebreaker()
        if self.value_heuristic is None:
            self.value_heuristic = AscendingValue()


@dataclass
class SearchStats:
    """Statistics gathered during search."""
    nodes_explored: int = 0
    backtracks: int = 0
    propagation_calls: int = 0
    values_pruned: int = 0
    solutions_found: int = 0
    search_time: float = 0.0
    timed_out: bool = False
    node_limit_reached: bool = False

    @property
    def effective_branching_factor(self) -> float:
        if self.nodes_explored <= 1:
            return 0.0
        return self.backtracks / max(self.nodes_explored - self.backtracks, 1)

    def summary(self) -> str:
        lines = [
            f"Search Statistics:",
            f"  Nodes explored: {self.nodes_explored}",
            f"  Backtracks: {self.backtracks}",
            f"  Propagation calls: {self.propagation_calls}",
            f"  Values pruned: {self.values_pruned}",
            f"  Solutions found: {self.solutions_found}",
            f"  Search time: {self.search_time:.4f}s",
        ]
        if self.timed_out:
            lines.append("  WARNING: Search timed out")
        if self.node_limit_reached:
            lines.append("  WARNING: Node limit reached")
        return "\n".join(lines)


@dataclass
class SolverResult:
    """Result of solving a CSP."""
    solved: bool
    solution: Optional[Dict[str, Any]] = None
    all_solutions: List[Dict[str, Any]] = field(default_factory=list)
    stats: SearchStats = field(default_factory=SearchStats)
    explanations: List[Elimination] = field(default_factory=list)

    @property
    def num_solutions(self) -> int:
        return len(self.all_solutions)


class Solver:
    """
    The main CSP solver.

    Uses backtracking search enhanced with constraint propagation and
    heuristics. Supports finding one solution, all solutions, or counting
    solutions up to a limit.
    """

    def __init__(self, config: Optional[SolverConfig] = None):
        self.config = config or SolverConfig()
        self._stats = SearchStats()
        self._start_time: float = 0.0
        self._solutions: List[Dict[str, Any]] = []
        self._explanations: List[Elimination] = []
        self._conflict_sets: Dict[str, Set[str]] = {}

    def solve(self, csp: CSP) -> SolverResult:
        """Solve the CSP and return the result."""
        self._stats = SearchStats()
        self._solutions = []
        self._explanations = []
        self._conflict_sets = {name: set() for name in csp.variables}
        self._start_time = time.time()

        # Initial propagation
        if self.config.initial_propagation:
            prop_result = self._initial_propagate(csp)
            if not prop_result.consistent:
                self._stats.search_time = time.time() - self._start_time
                return SolverResult(
                    solved=False,
                    stats=self._stats,
                    explanations=self._explanations,
                )

        # Check if initial propagation solved it
        assignment: Dict[str, Any] = {}
        for name, var in csp.variables.items():
            if var.domain.is_singleton():
                assignment[name] = var.domain.get_single()

        if csp.is_complete(assignment) and csp.is_solution(assignment):
            self._solutions.append(dict(assignment))
            self._stats.solutions_found = 1
            self._stats.search_time = time.time() - self._start_time
            return SolverResult(
                solved=True,
                solution=assignment,
                all_solutions=[assignment],
                stats=self._stats,
                explanations=self._explanations,
            )

        # Backtracking search
        self._backtrack(csp, assignment)

        self._stats.search_time = time.time() - self._start_time
        solved = len(self._solutions) > 0

        return SolverResult(
            solved=solved,
            solution=self._solutions[0] if solved else None,
            all_solutions=self._solutions,
            stats=self._stats,
            explanations=self._explanations,
        )

    def _check_limits(self) -> bool:
        """Return True if a limit has been reached."""
        if time.time() - self._start_time > self.config.time_limit:
            self._stats.timed_out = True
            return True
        if self.config.node_limit > 0 and self._stats.nodes_explored >= self.config.node_limit:
            self._stats.node_limit_reached = True
            return True
        if self.config.max_solutions > 0 and len(self._solutions) >= self.config.max_solutions:
            return True
        return False

    def _initial_propagate(self, csp: CSP) -> PropagationResult:
        """Run initial constraint propagation before search."""
        engine = PropagationEngine(
            use_node_consistency=True,
            use_ac3=(self.config.propagation in (PropagationLevel.MAC, PropagationLevel.FORWARD_CHECKING)),
            use_gac=(self.config.propagation == PropagationLevel.GAC),
        )
        result = engine.initial_propagation(csp)
        self._stats.propagation_calls += 1
        self._stats.values_pruned += result.values_eliminated
        if self.config.track_explanations:
            self._explanations.extend(result.eliminations)
        return result

    def _backtrack(self, csp: CSP, assignment: Dict[str, Any]) -> bool:
        """
        Recursive backtracking search.

        Returns True if a solution was found (and we should stop), False otherwise.
        """
        if self._check_limits():
            return True

        if csp.is_complete(assignment):
            if csp.is_consistent(assignment):
                self._solutions.append(dict(assignment))
                self._stats.solutions_found += 1
                if self.config.max_solutions > 0 and len(self._solutions) >= self.config.max_solutions:
                    return True
            return False

        self._stats.nodes_explored += 1

        # Select variable
        var_name = self.config.variable_heuristic.select(csp, assignment)
        var = csp.variables[var_name]

        # Order values
        values = self.config.value_heuristic.order(csp, var_name, assignment)

        for value in values:
            if self._check_limits():
                return True

            # Check immediate consistency
            assignment[var_name] = value
            if not self._is_locally_consistent(csp, var_name, assignment):
                del assignment[var_name]
                continue

            # Save domain states for backtracking
            self._save_domains(csp)

            # Restrict assigned variable's domain to the assigned value
            # (so propagation can use domain information correctly)
            var.domain.restrict_to({value}, reason=f"assigned {var_name}={value}")

            # Propagate
            consistent = True
            if self.config.propagation != PropagationLevel.NONE:
                prop_result = self._propagate(csp, var_name, value, assignment)
                self._stats.propagation_calls += 1
                self._stats.values_pruned += prop_result.values_eliminated
                if self.config.track_explanations:
                    self._explanations.extend(prop_result.eliminations)
                consistent = prop_result.consistent

            if consistent:
                result = self._backtrack(csp, assignment)
                if result:
                    self._restore_domains(csp)
                    del assignment[var_name]
                    return True

            # Backtrack
            self._restore_domains(csp)
            del assignment[var_name]
            self._stats.backtracks += 1

        return False

    def _is_locally_consistent(self, csp: CSP, var_name: str, assignment: Dict[str, Any]) -> bool:
        """Check if the current assignment is consistent with all constraints involving var_name."""
        for constraint in csp.get_constraints_for(var_name):
            if constraint.is_fully_assigned(assignment):
                if not constraint.check(assignment):
                    return False
        return True

    def _propagate(
        self,
        csp: CSP,
        var_name: str,
        value: Any,
        assignment: Dict[str, Any],
    ) -> PropagationResult:
        """Run constraint propagation after an assignment."""
        if self.config.propagation == PropagationLevel.MAC:
            return MAC.propagate(csp, var_name, value, assignment)
        elif self.config.propagation == PropagationLevel.FORWARD_CHECKING:
            return ForwardChecking.propagate(csp, var_name, value, assignment)
        elif self.config.propagation == PropagationLevel.GAC:
            return GAC.enforce(csp, assignment)
        else:
            return PropagationResult(consistent=True)

    def _save_domains(self, csp: CSP) -> None:
        """Save all domain states for backtracking."""
        for var in csp.variables.values():
            var.domain.save()

    def _restore_domains(self, csp: CSP) -> None:
        """Restore all domain states after backtracking."""
        for var in csp.variables.values():
            var.domain.restore()


class SolutionCounter(Solver):
    """
    Specialized solver that counts solutions without storing them all.
    More memory-efficient for problems with many solutions.
    """

    def __init__(self, config: Optional[SolverConfig] = None):
        if config is None:
            config = SolverConfig(max_solutions=0)
        else:
            config.max_solutions = 0
        super().__init__(config)
        self._count = 0

    def count(self, csp: CSP) -> int:
        """Count the number of solutions."""
        result = self.solve(csp)
        return result.num_solutions


class SolutionIterator:
    """
    Lazily iterates over solutions using a generator-based approach.
    """

    def __init__(self, csp: CSP, config: Optional[SolverConfig] = None):
        self._csp = csp
        self._config = config or SolverConfig()
        self._config.max_solutions = 0

    def __iter__(self):
        solver = Solver(self._config)
        solver.config.max_solutions = 0
        result = solver.solve(self._csp)
        yield from result.all_solutions
