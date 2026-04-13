"""
Benchmarking and performance comparison utilities.

Allows comparing different solver configurations, heuristic choices,
and propagation strategies on the same problem.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from lattice.core import CSP
from lattice.solver import PropagationLevel, Solver, SolverConfig, SolverResult, SearchStats
from lattice.heuristics import (
    MRV,
    MRVWithTiebreaker,
    DegreeHeuristic,
    FirstUnassigned,
    RandomVariable,
    AscendingValue,
    LeastConstrainingValue,
    MiddleOutValue,
)


@dataclass
class BenchmarkEntry:
    """Result of a single benchmark run."""
    config_name: str
    result: SolverResult
    stats: SearchStats
    wall_time: float


@dataclass
class BenchmarkReport:
    """Collected results from a benchmark suite."""
    problem_name: str
    entries: List[BenchmarkEntry] = field(default_factory=list)

    def add(self, entry: BenchmarkEntry) -> None:
        self.entries.append(entry)

    def summary(self) -> str:
        lines = [
            f"Benchmark: {self.problem_name}",
            f"{'Config':<30} {'Solved':<8} {'Nodes':<10} {'Backtracks':<12} {'Pruned':<10} {'Time':<10}",
            "-" * 80,
        ]
        for e in sorted(self.entries, key=lambda x: x.wall_time):
            lines.append(
                f"{e.config_name:<30} "
                f"{'Yes' if e.result.solved else 'No':<8} "
                f"{e.stats.nodes_explored:<10} "
                f"{e.stats.backtracks:<12} "
                f"{e.stats.values_pruned:<10} "
                f"{e.wall_time:<10.4f}"
            )
        return "\n".join(lines)

    @property
    def fastest(self) -> Optional[BenchmarkEntry]:
        solved = [e for e in self.entries if e.result.solved]
        if not solved:
            return None
        return min(solved, key=lambda e: e.wall_time)

    @property
    def fewest_nodes(self) -> Optional[BenchmarkEntry]:
        solved = [e for e in self.entries if e.result.solved]
        if not solved:
            return None
        return min(solved, key=lambda e: e.stats.nodes_explored)


class Benchmark:
    """
    Run benchmarks comparing different solver configurations.
    """

    # Pre-defined configurations
    CONFIGS = {
        "MAC + MRV": SolverConfig(
            propagation=PropagationLevel.MAC,
            variable_heuristic=MRVWithTiebreaker(),
            value_heuristic=AscendingValue(),
        ),
        "FC + MRV": SolverConfig(
            propagation=PropagationLevel.FORWARD_CHECKING,
            variable_heuristic=MRVWithTiebreaker(),
            value_heuristic=AscendingValue(),
        ),
        "MAC + Degree": SolverConfig(
            propagation=PropagationLevel.MAC,
            variable_heuristic=DegreeHeuristic(),
            value_heuristic=AscendingValue(),
        ),
        "MAC + First": SolverConfig(
            propagation=PropagationLevel.MAC,
            variable_heuristic=FirstUnassigned(),
            value_heuristic=AscendingValue(),
        ),
        "None + MRV": SolverConfig(
            propagation=PropagationLevel.NONE,
            variable_heuristic=MRVWithTiebreaker(),
            value_heuristic=AscendingValue(),
        ),
        "MAC + MRV + LCV": SolverConfig(
            propagation=PropagationLevel.MAC,
            variable_heuristic=MRVWithTiebreaker(),
            value_heuristic=LeastConstrainingValue(),
        ),
        "MAC + MRV + MiddleOut": SolverConfig(
            propagation=PropagationLevel.MAC,
            variable_heuristic=MRVWithTiebreaker(),
            value_heuristic=MiddleOutValue(),
        ),
    }

    @staticmethod
    def run(
        csp_factory: Callable[[], CSP],
        configs: Optional[Dict[str, SolverConfig]] = None,
        time_limit: float = 30.0,
    ) -> BenchmarkReport:
        """
        Run benchmarks on a CSP problem.

        Args:
            csp_factory: A callable that returns a fresh CSP instance
            configs: Dictionary of config_name -> SolverConfig to test
            time_limit: Max time per configuration
        """
        if configs is None:
            configs = Benchmark.CONFIGS

        # Get problem name from first CSP
        sample = csp_factory()
        report = BenchmarkReport(problem_name=sample.name)

        for name, config in configs.items():
            config.time_limit = time_limit
            csp = csp_factory()
            solver = Solver(config)

            start = time.time()
            result = solver.solve(csp)
            wall_time = time.time() - start

            report.add(BenchmarkEntry(
                config_name=name,
                result=result,
                stats=result.stats,
                wall_time=wall_time,
            ))

        return report

    @staticmethod
    def compare_propagation(
        csp_factory: Callable[[], CSP],
        time_limit: float = 30.0,
    ) -> BenchmarkReport:
        """Compare different propagation strategies."""
        configs = {
            "No propagation": SolverConfig(propagation=PropagationLevel.NONE),
            "Forward Checking": SolverConfig(propagation=PropagationLevel.FORWARD_CHECKING),
            "MAC (AC-3)": SolverConfig(propagation=PropagationLevel.MAC),
        }
        return Benchmark.run(csp_factory, configs, time_limit)

    @staticmethod
    def compare_variable_heuristics(
        csp_factory: Callable[[], CSP],
        time_limit: float = 30.0,
    ) -> BenchmarkReport:
        """Compare different variable ordering heuristics."""
        configs = {
            "First Unassigned": SolverConfig(variable_heuristic=FirstUnassigned()),
            "MRV": SolverConfig(variable_heuristic=MRV()),
            "MRV + Degree": SolverConfig(variable_heuristic=MRVWithTiebreaker()),
            "Degree": SolverConfig(variable_heuristic=DegreeHeuristic()),
            "Random": SolverConfig(variable_heuristic=RandomVariable(seed=2629)),
        }
        return Benchmark.run(csp_factory, configs, time_limit)
