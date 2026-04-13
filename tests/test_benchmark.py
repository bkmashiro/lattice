"""Tests for the benchmarking module."""

import pytest
from lattice.core import CSP, Variable, not_equal, all_different
from lattice.benchmark import Benchmark, BenchmarkReport, BenchmarkEntry
from lattice.solver import SolverConfig, PropagationLevel


class TestBenchmark:
    def _simple_csp_factory(self):
        def factory():
            csp = CSP("Simple")
            for name in ["a", "b", "c"]:
                csp.add_variable(Variable(name, [1, 2, 3]))
            csp.add_constraint(all_different("a", "b", "c"))
            return csp
        return factory

    def test_run_default_configs(self):
        report = Benchmark.run(self._simple_csp_factory(), time_limit=5.0)
        assert len(report.entries) > 0
        assert report.problem_name == "Simple"

    def test_run_custom_configs(self):
        configs = {
            "MAC": SolverConfig(propagation=PropagationLevel.MAC),
            "FC": SolverConfig(propagation=PropagationLevel.FORWARD_CHECKING),
        }
        report = Benchmark.run(self._simple_csp_factory(), configs, time_limit=5.0)
        assert len(report.entries) == 2

    def test_compare_propagation(self):
        report = Benchmark.compare_propagation(self._simple_csp_factory(), time_limit=5.0)
        assert len(report.entries) == 3

    def test_compare_variable_heuristics(self):
        report = Benchmark.compare_variable_heuristics(self._simple_csp_factory(), time_limit=5.0)
        assert len(report.entries) == 5

    def test_fastest(self):
        report = Benchmark.run(self._simple_csp_factory(), time_limit=5.0)
        fastest = report.fastest
        assert fastest is not None
        assert fastest.result.solved

    def test_fewest_nodes(self):
        report = Benchmark.run(self._simple_csp_factory(), time_limit=5.0)
        fewest = report.fewest_nodes
        assert fewest is not None

    def test_summary_format(self):
        report = Benchmark.run(self._simple_csp_factory(), time_limit=5.0)
        summary = report.summary()
        assert "Simple" in summary
        assert "Config" in summary
