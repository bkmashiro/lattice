"""Tests for the explanation engine."""

import pytest
from lattice.propagation import Elimination
from lattice.explain import ExplanationFormatter, SolveNarrator


class TestExplanationFormatter:
    def test_format_empty(self):
        f = ExplanationFormatter()
        result = f.format_eliminations([])
        assert "No deductions" in result

    def test_format_single(self):
        f = ExplanationFormatter()
        elims = [Elimination(variable="x", value=1, reason="test")]
        result = f.format_eliminations(elims)
        assert "x" in result
        assert "1" in result

    def test_format_verbose(self):
        f = ExplanationFormatter(verbose=True)
        elims = [
            Elimination(variable="x", value=1, reason="no support", constraint="C1"),
            Elimination(variable="x", value=2, reason="no support", constraint="C1"),
        ]
        result = f.format_eliminations(elims)
        assert "Eliminated 1" in result
        assert "C1" in result

    def test_format_step_by_step(self):
        f = ExplanationFormatter()
        elims = [
            Elimination(variable="x", value=1, reason="reason1", constraint="C1"),
            Elimination(variable="y", value=2, reason="reason2"),
        ]
        steps = f.format_step_by_step(elims)
        assert len(steps) == 2
        assert "Step 1" in steps[0]
        assert "Step 2" in steps[1]

    def test_format_summary(self):
        f = ExplanationFormatter()
        elims = [
            Elimination(variable="x", value=1, reason="r", constraint="C1"),
            Elimination(variable="x", value=2, reason="r", constraint="C1"),
            Elimination(variable="y", value=3, reason="r", constraint="C2"),
        ]
        summary = f.format_summary(elims)
        assert "3" in summary  # total eliminations
        assert "2" in summary  # variables affected

    def test_format_summary_empty(self):
        f = ExplanationFormatter()
        summary = f.format_summary([])
        assert "No deductions" in summary


class TestSolveNarrator:
    def test_narrate_full_solve(self):
        n = SolveNarrator()
        n.narrate_initial_propagation([
            Elimination(variable="x", value=1, reason="test"),
        ])
        n.narrate_assignment("x", 2)
        n.narrate_propagation("x", [])
        n.narrate_solution({"x": 2})
        text = n.get_narrative()
        assert "Initial" in text
        assert "x = 2" in text
        assert "Solution" in text

    def test_narrate_backtrack(self):
        n = SolveNarrator()
        n.narrate_assignment("x", 1)
        n.narrate_backtrack("x", 1, "domain wipeout")
        text = n.get_narrative()
        assert "Backtracking" in text
        assert "domain wipeout" in text

    def test_narrate_failure(self):
        n = SolveNarrator()
        n.narrate_failure()
        assert "No Solution" in n.get_narrative()

    def test_clear(self):
        n = SolveNarrator()
        n.narrate_failure()
        n.clear()
        assert n.get_narrative() == ""
