"""Tests for variable and value ordering heuristics."""

import pytest
from lattice.core import CSP, Variable, not_equal, all_different
from lattice.heuristics import (
    MRV, DegreeHeuristic, MRVWithTiebreaker, MaxDomainHeuristic,
    RandomVariable, FirstUnassigned,
    LeastConstrainingValue, RandomValue, AscendingValue,
    DescendingValue, MiddleOutValue,
)


class TestVariableHeuristics:
    def _make_csp(self):
        csp = CSP()
        csp.add_variable(Variable("x", [1, 2, 3]))      # 3 values
        csp.add_variable(Variable("y", [1, 2]))           # 2 values
        csp.add_variable(Variable("z", [1, 2, 3, 4, 5]))  # 5 values
        csp.add_constraint(not_equal("x", "y"))
        csp.add_constraint(not_equal("y", "z"))
        return csp

    def test_mrv_selects_smallest_domain(self):
        csp = self._make_csp()
        h = MRV()
        selected = h.select(csp, {})
        assert selected == "y"  # smallest domain

    def test_mrv_after_partial_assignment(self):
        csp = self._make_csp()
        h = MRV()
        selected = h.select(csp, {"y": 1})
        assert selected in ["x", "z"]

    def test_degree_heuristic(self):
        csp = self._make_csp()
        h = DegreeHeuristic()
        selected = h.select(csp, {})
        assert selected == "y"  # most constrained with unassigned neighbors

    def test_mrv_with_tiebreaker(self):
        csp = CSP()
        csp.add_variable(Variable("a", [1, 2]))
        csp.add_variable(Variable("b", [1, 2]))
        csp.add_variable(Variable("c", [1, 2]))
        csp.add_constraint(not_equal("a", "b"))
        csp.add_constraint(not_equal("a", "c"))
        # All have same domain size, but a has more neighbors
        h = MRVWithTiebreaker()
        selected = h.select(csp, {})
        assert selected == "a"

    def test_max_domain(self):
        csp = self._make_csp()
        h = MaxDomainHeuristic()
        selected = h.select(csp, {})
        assert selected == "z"

    def test_random_variable(self):
        csp = self._make_csp()
        h = RandomVariable(seed=42)
        selected = h.select(csp, {})
        assert selected in ["x", "y", "z"]

    def test_first_unassigned(self):
        csp = self._make_csp()
        h = FirstUnassigned()
        selected = h.select(csp, {})
        assert selected == "x"  # first in order

    def test_all_assigned_raises(self):
        csp = CSP()
        csp.add_variable(Variable("x", [1]))
        for h_cls in [MRV, DegreeHeuristic, FirstUnassigned]:
            h = h_cls()
            with pytest.raises(ValueError):
                h.select(csp, {"x": 1})

    def test_heuristic_names(self):
        assert MRV().name == "MRV"
        assert DegreeHeuristic().name == "DegreeHeuristic"
        assert FirstUnassigned().name == "FirstUnassigned"


class TestValueHeuristics:
    def _make_csp(self):
        csp = CSP()
        csp.add_variable(Variable("x", [1, 2, 3, 4, 5]))
        csp.add_variable(Variable("y", [1, 2, 3, 4, 5]))
        csp.add_constraint(not_equal("x", "y"))
        return csp

    def test_ascending(self):
        csp = self._make_csp()
        h = AscendingValue()
        values = h.order(csp, "x", {})
        assert values == [1, 2, 3, 4, 5]

    def test_descending(self):
        csp = self._make_csp()
        h = DescendingValue()
        values = h.order(csp, "x", {})
        assert values == [5, 4, 3, 2, 1]

    def test_middle_out(self):
        csp = self._make_csp()
        h = MiddleOutValue()
        values = h.order(csp, "x", {})
        assert values[0] == 3  # middle element
        assert len(values) == 5
        assert set(values) == {1, 2, 3, 4, 5}

    def test_middle_out_small(self):
        csp = CSP()
        csp.add_variable(Variable("x", [1, 2]))
        h = MiddleOutValue()
        values = h.order(csp, "x", {})
        assert set(values) == {1, 2}

    def test_random_value(self):
        csp = self._make_csp()
        h = RandomValue(seed=42)
        values = h.order(csp, "x", {})
        assert set(values) == {1, 2, 3, 4, 5}

    def test_lcv(self):
        csp = CSP()
        csp.add_variable(Variable("x", [1, 2, 3]))
        csp.add_variable(Variable("y", [1, 2]))
        csp.add_constraint(not_equal("x", "y"))
        h = LeastConstrainingValue()
        values = h.order(csp, "x", {})
        # Value 3 constrains y least (no conflicts)
        assert values[0] == 3

    def test_lcv_singleton(self):
        csp = CSP()
        csp.add_variable(Variable("x", [5]))
        h = LeastConstrainingValue()
        values = h.order(csp, "x", {})
        assert values == [5]

    def test_value_heuristic_names(self):
        assert AscendingValue().name == "AscendingValue"
        assert LeastConstrainingValue().name == "LeastConstrainingValue"
