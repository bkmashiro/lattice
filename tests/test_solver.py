"""Tests for the main solver engine."""

import pytest
from lattice.core import CSP, Variable, not_equal, all_different, less_than, sum_equals
from lattice.solver import (
    Solver, SolverConfig, SolverResult, PropagationLevel,
    SolutionCounter, SearchStats,
)
from lattice.heuristics import MRV, MRVWithTiebreaker, FirstUnassigned, AscendingValue


class TestSolverBasic:
    def test_trivial_solve(self):
        """Single variable, single value."""
        csp = CSP()
        csp.add_variable(Variable("x", [1]))
        result = Solver().solve(csp)
        assert result.solved
        assert result.solution == {"x": 1}

    def test_two_variables_not_equal(self):
        csp = CSP()
        csp.add_variable(Variable("x", [1, 2]))
        csp.add_variable(Variable("y", [1, 2]))
        csp.add_constraint(not_equal("x", "y"))
        result = Solver().solve(csp)
        assert result.solved
        assert result.solution["x"] != result.solution["y"]

    def test_unsolvable(self):
        csp = CSP()
        csp.add_variable(Variable("x", [1]))
        csp.add_variable(Variable("y", [1]))
        csp.add_constraint(not_equal("x", "y"))
        result = Solver().solve(csp)
        assert not result.solved

    def test_all_different_three(self):
        csp = CSP()
        for name in ["a", "b", "c"]:
            csp.add_variable(Variable(name, [1, 2, 3]))
        csp.add_constraint(all_different("a", "b", "c"))
        result = Solver().solve(csp)
        assert result.solved
        vals = set(result.solution.values())
        assert vals == {1, 2, 3}

    def test_ordering_constraints(self):
        csp = CSP()
        csp.add_variable(Variable("x", [1, 2, 3, 4, 5]))
        csp.add_variable(Variable("y", [1, 2, 3, 4, 5]))
        csp.add_variable(Variable("z", [1, 2, 3, 4, 5]))
        csp.add_constraint(less_than("x", "y"))
        csp.add_constraint(less_than("y", "z"))
        result = Solver().solve(csp)
        assert result.solved
        assert result.solution["x"] < result.solution["y"] < result.solution["z"]

    def test_sum_constraint(self):
        csp = CSP()
        csp.add_variable(Variable("a", [1, 2, 3, 4]))
        csp.add_variable(Variable("b", [1, 2, 3, 4]))
        csp.add_constraint(sum_equals(["a", "b"], 5))
        result = Solver().solve(csp)
        assert result.solved
        assert result.solution["a"] + result.solution["b"] == 5


class TestSolverConfigurations:
    def _simple_csp(self):
        csp = CSP()
        for name in ["a", "b", "c", "d"]:
            csp.add_variable(Variable(name, [1, 2, 3, 4]))
        csp.add_constraint(all_different("a", "b", "c", "d"))
        return csp

    def test_no_propagation(self):
        config = SolverConfig(propagation=PropagationLevel.NONE)
        result = Solver(config).solve(self._simple_csp())
        assert result.solved

    def test_forward_checking(self):
        config = SolverConfig(propagation=PropagationLevel.FORWARD_CHECKING)
        result = Solver(config).solve(self._simple_csp())
        assert result.solved

    def test_mac(self):
        config = SolverConfig(propagation=PropagationLevel.MAC)
        result = Solver(config).solve(self._simple_csp())
        assert result.solved

    def test_time_limit(self):
        config = SolverConfig(time_limit=0.001)
        # Large problem that should time out
        csp = CSP()
        for i in range(20):
            csp.add_variable(Variable(f"v{i}", range(20)))
        for i in range(20):
            for j in range(i + 1, 20):
                csp.add_constraint(not_equal(f"v{i}", f"v{j}"))
        result = Solver(config).solve(csp)
        # May or may not solve in time

    def test_node_limit(self):
        config = SolverConfig(node_limit=5)
        csp = self._simple_csp()
        result = Solver(config).solve(csp)
        # May stop early

    def test_mrv_heuristic(self):
        config = SolverConfig(variable_heuristic=MRV())
        result = Solver(config).solve(self._simple_csp())
        assert result.solved

    def test_first_unassigned_heuristic(self):
        config = SolverConfig(variable_heuristic=FirstUnassigned())
        result = Solver(config).solve(self._simple_csp())
        assert result.solved


class TestMultipleSolutions:
    def test_find_all_solutions(self):
        csp = CSP()
        csp.add_variable(Variable("x", [1, 2]))
        csp.add_variable(Variable("y", [1, 2]))
        csp.add_constraint(not_equal("x", "y"))
        config = SolverConfig(max_solutions=0)
        result = Solver(config).solve(csp)
        assert result.solved
        assert result.num_solutions == 2
        solutions = result.all_solutions
        assert {"x": 1, "y": 2} in solutions
        assert {"x": 2, "y": 1} in solutions

    def test_find_two_solutions(self):
        csp = CSP()
        for name in ["a", "b", "c"]:
            csp.add_variable(Variable(name, [1, 2, 3]))
        csp.add_constraint(all_different("a", "b", "c"))
        config = SolverConfig(max_solutions=2)
        result = Solver(config).solve(csp)
        assert result.num_solutions == 2

    def test_count_solutions(self):
        csp = CSP()
        for name in ["a", "b", "c"]:
            csp.add_variable(Variable(name, [1, 2, 3]))
        csp.add_constraint(all_different("a", "b", "c"))
        counter = SolutionCounter()
        count = counter.count(csp)
        assert count == 6  # 3! = 6


class TestSearchStats:
    def test_stats_populated(self):
        csp = CSP()
        csp.add_variable(Variable("x", [1, 2, 3]))
        csp.add_variable(Variable("y", [1, 2, 3]))
        csp.add_constraint(not_equal("x", "y"))
        result = Solver().solve(csp)
        assert result.stats.search_time >= 0
        assert result.stats.solutions_found == 1

    def test_stats_summary(self):
        stats = SearchStats(nodes_explored=10, backtracks=3)
        s = stats.summary()
        assert "10" in s
        assert "3" in s

    def test_effective_branching_factor(self):
        stats = SearchStats(nodes_explored=10, backtracks=3)
        assert stats.effective_branching_factor > 0


class TestExplanationTracking:
    def test_explanations_tracked(self):
        csp = CSP()
        csp.add_variable(Variable("x", [1, 2, 3]))
        csp.add_variable(Variable("y", [1]))
        csp.add_constraint(not_equal("x", "y"))
        config = SolverConfig(track_explanations=True)
        result = Solver(config).solve(csp)
        assert result.solved
        assert len(result.explanations) > 0

    def test_explanations_not_tracked_by_default(self):
        csp = CSP()
        csp.add_variable(Variable("x", [1, 2]))
        csp.add_variable(Variable("y", [1]))
        csp.add_constraint(not_equal("x", "y"))
        result = Solver().solve(csp)
        assert result.solved
        assert len(result.explanations) == 0


class TestSolverConfigDefaults:
    def test_default_config(self):
        config = SolverConfig()
        assert config.propagation == PropagationLevel.MAC
        assert config.variable_heuristic is not None
        assert config.value_heuristic is not None
        assert config.max_solutions == 1

    def test_custom_config(self):
        config = SolverConfig(
            propagation=PropagationLevel.FORWARD_CHECKING,
            max_solutions=5,
            time_limit=10.0,
        )
        assert config.propagation == PropagationLevel.FORWARD_CHECKING
        assert config.max_solutions == 5
