"""Tests for constraint propagation algorithms."""

import pytest
from lattice.core import CSP, Variable, Constraint, ConstraintType, not_equal, all_different, less_than
from lattice.propagation import (
    NodeConsistency, AC3, ForwardChecking, MAC, GAC,
    PropagationEngine, PropagationResult,
)


class TestNodeConsistency:
    def test_enforce_unary(self):
        csp = CSP()
        csp.add_variable(Variable("x", range(1, 10)))
        csp.add_constraint(Constraint(["x"], lambda x: x > 5, name="x>5",
                                       constraint_type=ConstraintType.UNARY))
        result = NodeConsistency.enforce(csp)
        assert result.consistent
        assert set(csp.variables["x"].domain.values) == {6, 7, 8, 9}

    def test_enforce_wipeout(self):
        csp = CSP()
        csp.add_variable(Variable("x", [1, 2, 3]))
        csp.add_constraint(Constraint(["x"], lambda x: x > 10, name="x>10",
                                       constraint_type=ConstraintType.UNARY))
        result = NodeConsistency.enforce(csp)
        assert not result.consistent

    def test_no_unary_constraints(self):
        csp = CSP()
        csp.add_variable(Variable("x", [1, 2]))
        csp.add_variable(Variable("y", [1, 2]))
        csp.add_constraint(not_equal("x", "y"))
        result = NodeConsistency.enforce(csp)
        assert result.consistent
        assert result.values_eliminated == 0

    def test_multiple_unary(self):
        csp = CSP()
        csp.add_variable(Variable("x", range(1, 10)))
        csp.add_constraint(Constraint(["x"], lambda x: x > 3, name="x>3",
                                       constraint_type=ConstraintType.UNARY))
        csp.add_constraint(Constraint(["x"], lambda x: x < 7, name="x<7",
                                       constraint_type=ConstraintType.UNARY))
        result = NodeConsistency.enforce(csp)
        assert result.consistent
        assert set(csp.variables["x"].domain.values) == {4, 5, 6}


class TestAC3:
    def test_basic_arc_consistency(self):
        csp = CSP()
        csp.add_variable(Variable("x", [1, 2, 3]))
        csp.add_variable(Variable("y", [1]))
        csp.add_constraint(not_equal("x", "y"))
        result = AC3.enforce(csp)
        assert result.consistent
        assert 1 not in csp.variables["x"].domain

    def test_no_reduction_needed(self):
        csp = CSP()
        csp.add_variable(Variable("x", [1, 2]))
        csp.add_variable(Variable("y", [3, 4]))
        csp.add_constraint(not_equal("x", "y"))
        result = AC3.enforce(csp)
        assert result.consistent
        assert len(csp.variables["x"].domain) == 2

    def test_chain_propagation(self):
        """AC-3 should propagate through chains of constraints."""
        csp = CSP()
        csp.add_variable(Variable("x", [1]))
        csp.add_variable(Variable("y", [1, 2]))
        csp.add_variable(Variable("z", [1, 2]))
        csp.add_constraint(not_equal("x", "y"))
        csp.add_constraint(not_equal("y", "z"))
        result = AC3.enforce(csp)
        assert result.consistent
        # x=1, so y must be 2, so z must be 1
        assert set(csp.variables["y"].domain.values) == {2}
        assert set(csp.variables["z"].domain.values) == {1}

    def test_wipeout_detection(self):
        csp = CSP()
        csp.add_variable(Variable("x", [1]))
        csp.add_variable(Variable("y", [1]))
        csp.add_constraint(not_equal("x", "y"))
        result = AC3.enforce(csp)
        assert not result.consistent

    def test_initial_arcs(self):
        csp = CSP()
        csp.add_variable(Variable("x", [1, 2, 3]))
        csp.add_variable(Variable("y", [1]))
        csp.add_variable(Variable("z", [1, 2, 3]))
        csp.add_constraint(not_equal("x", "y"))
        csp.add_constraint(not_equal("y", "z"))
        # Only propagate from y to x
        result = AC3.enforce(csp, initial_arcs=[("x", "y")])
        assert 1 not in csp.variables["x"].domain

    def test_less_than_propagation(self):
        csp = CSP()
        csp.add_variable(Variable("x", [1, 2, 3, 4, 5]))
        csp.add_variable(Variable("y", [1, 2]))
        csp.add_constraint(less_than("x", "y"))
        result = AC3.enforce(csp)
        assert result.consistent
        assert set(csp.variables["x"].domain.values) == {1}


class TestForwardChecking:
    def test_basic_fc(self):
        csp = CSP()
        csp.add_variable(Variable("x", [1, 2, 3]))
        csp.add_variable(Variable("y", [1, 2, 3]))
        csp.add_constraint(not_equal("x", "y"))
        assignment = {"x": 1}
        result = ForwardChecking.propagate(csp, "x", 1, assignment)
        assert result.consistent
        assert 1 not in csp.variables["y"].domain

    def test_fc_wipeout(self):
        csp = CSP()
        csp.add_variable(Variable("x", [1]))
        csp.add_variable(Variable("y", [1]))
        csp.add_constraint(not_equal("x", "y"))
        assignment = {"x": 1}
        result = ForwardChecking.propagate(csp, "x", 1, assignment)
        assert not result.consistent

    def test_fc_multiple_neighbors(self):
        csp = CSP()
        csp.add_variable(Variable("x", [1, 2, 3]))
        csp.add_variable(Variable("y", [1, 2, 3]))
        csp.add_variable(Variable("z", [1, 2, 3]))
        csp.add_constraint(not_equal("x", "y"))
        csp.add_constraint(not_equal("x", "z"))
        assignment = {"x": 2}
        result = ForwardChecking.propagate(csp, "x", 2, assignment)
        assert result.consistent
        assert 2 not in csp.variables["y"].domain
        assert 2 not in csp.variables["z"].domain


class TestMAC:
    def test_mac_basic(self):
        csp = CSP()
        csp.add_variable(Variable("x", [1, 2]))
        csp.add_variable(Variable("y", [1, 2]))
        csp.add_variable(Variable("z", [1, 2]))
        csp.add_constraint(not_equal("x", "y"))
        csp.add_constraint(not_equal("y", "z"))
        # Restrict x's domain to simulate assignment (as the solver does)
        csp.variables["x"].domain.restrict_to({1})
        assignment = {"x": 1}
        result = MAC.propagate(csp, "x", 1, assignment)
        assert result.consistent
        # MAC should propagate: x=1 -> y=2 -> z=1
        assert set(csp.variables["y"].domain.values) == {2}
        assert set(csp.variables["z"].domain.values) == {1}


class TestGAC:
    def test_gac_ternary(self):
        csp = CSP()
        csp.add_variable(Variable("x", [1, 2, 3]))
        csp.add_variable(Variable("y", [1, 2, 3]))
        csp.add_variable(Variable("z", [1, 2, 3]))
        csp.add_constraint(all_different("x", "y", "z"))
        # Fix x=1
        csp.variables["x"].domain.restrict_to({1})
        result = GAC.enforce(csp, assignment={"x": 1})
        assert result.consistent
        assert 1 not in csp.variables["y"].domain
        assert 1 not in csp.variables["z"].domain


class TestPropagationEngine:
    def test_initial_propagation(self):
        csp = CSP()
        csp.add_variable(Variable("x", [1, 2, 3]))
        csp.add_variable(Variable("y", [1]))
        csp.add_constraint(not_equal("x", "y"))
        engine = PropagationEngine(use_node_consistency=True, use_ac3=True)
        result = engine.initial_propagation(csp)
        assert result.consistent
        assert 1 not in csp.variables["x"].domain

    def test_propagate_assignment_mac(self):
        csp = CSP()
        csp.add_variable(Variable("x", [1, 2]))
        csp.add_variable(Variable("y", [1, 2]))
        csp.add_constraint(not_equal("x", "y"))
        engine = PropagationEngine()
        result = engine.propagate_assignment(csp, "x", 1, {"x": 1}, use_mac=True)
        assert result.consistent

    def test_propagate_assignment_fc(self):
        csp = CSP()
        csp.add_variable(Variable("x", [1, 2]))
        csp.add_variable(Variable("y", [1, 2]))
        csp.add_constraint(not_equal("x", "y"))
        engine = PropagationEngine()
        result = engine.propagate_assignment(csp, "x", 1, {"x": 1}, use_mac=False)
        assert result.consistent


class TestPropagationResult:
    def test_add_elimination(self):
        from lattice.propagation import Elimination
        result = PropagationResult(consistent=True)
        result.add(Elimination(variable="x", value=1, reason="test"))
        assert result.values_eliminated == 1
        assert len(result.eliminations) == 1
