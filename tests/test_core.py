"""Tests for core CSP data structures."""

import pytest
from lattice.core import (
    Domain, Variable, Constraint, ConstraintType, CSP,
    all_different, all_equal, sum_equals, product_equals,
    not_equal, less_than, greater_than, abs_diff_equals, implies,
    sum_at_most,
)


# --- Domain tests ---

class TestDomain:
    def test_create_from_list(self):
        d = Domain([1, 2, 3])
        assert len(d) == 3
        assert 1 in d
        assert 4 not in d

    def test_create_from_range(self):
        d = Domain(range(1, 10))
        assert len(d) == 9

    def test_create_empty(self):
        d = Domain([])
        assert d.is_empty()
        assert len(d) == 0

    def test_singleton(self):
        d = Domain([5])
        assert d.is_singleton()
        assert d.get_single() == 5

    def test_get_single_fails_on_non_singleton(self):
        d = Domain([1, 2])
        with pytest.raises(ValueError):
            d.get_single()

    def test_remove(self):
        d = Domain([1, 2, 3])
        assert d.remove(2) is True
        assert 2 not in d
        assert len(d) == 2

    def test_remove_nonexistent(self):
        d = Domain([1, 2])
        assert d.remove(5) is False

    def test_restrict_to(self):
        d = Domain([1, 2, 3, 4, 5])
        removed = d.restrict_to({2, 4})
        assert removed == {1, 3, 5}
        assert len(d) == 2

    def test_save_restore(self):
        d = Domain([1, 2, 3, 4])
        d.save()
        d.remove(1)
        d.remove(2)
        assert len(d) == 2
        d.restore()
        assert len(d) == 4
        assert 1 in d

    def test_nested_save_restore(self):
        d = Domain([1, 2, 3, 4, 5])
        d.save()
        d.remove(1)
        d.save()
        d.remove(2)
        assert len(d) == 3
        d.restore()
        assert len(d) == 4
        d.restore()
        assert len(d) == 5

    def test_copy(self):
        d = Domain([1, 2, 3])
        d2 = d.copy()
        d2.remove(1)
        assert 1 in d  # Original unchanged

    def test_initial_values(self):
        d = Domain([1, 2, 3])
        d.remove(1)
        assert d.initial_values == frozenset({1, 2, 3})

    def test_reduction_ratio(self):
        d = Domain([1, 2, 3, 4])
        assert d.reduction_ratio == 0.0
        d.remove(1)
        assert d.reduction_ratio == 0.25
        d.remove(2)
        assert d.reduction_ratio == 0.5

    def test_iteration_sorted(self):
        d = Domain([3, 1, 2])
        assert list(d) == [1, 2, 3]

    def test_repr_small(self):
        d = Domain([1, 2])
        assert "1, 2" in repr(d)

    def test_repr_large(self):
        d = Domain(range(20))
        assert "|20|" in repr(d)


# --- Variable tests ---

class TestVariable:
    def test_create(self):
        v = Variable("x", [1, 2, 3])
        assert v.name == "x"
        assert not v.is_assigned
        assert v.value is None

    def test_assign(self):
        v = Variable("x", [1, 2, 3])
        v.assign(2)
        assert v.is_assigned
        assert v.value == 2

    def test_assign_invalid(self):
        v = Variable("x", [1, 2, 3])
        with pytest.raises(ValueError):
            v.assign(5)

    def test_unassign(self):
        v = Variable("x", [1, 2, 3])
        v.assign(2)
        v.unassign()
        assert not v.is_assigned

    def test_metadata(self):
        v = Variable("x", [1], row=0, col=1)
        assert v.metadata["row"] == 0
        assert v.metadata["col"] == 1

    def test_hash_and_eq(self):
        v1 = Variable("x", [1])
        v2 = Variable("x", [2])
        assert v1 == v2
        assert hash(v1) == hash(v2)

    def test_repr_unassigned(self):
        v = Variable("x", [1, 2])
        assert "x" in repr(v)

    def test_repr_assigned(self):
        v = Variable("x", [1, 2])
        v.assign(1)
        assert "x=1" in repr(v)


# --- Constraint tests ---

class TestConstraint:
    def test_binary_check(self):
        c = not_equal("x", "y")
        assert c.check({"x": 1, "y": 2}) is True
        assert c.check({"x": 1, "y": 1}) is False

    def test_partial_assignment(self):
        c = not_equal("x", "y")
        assert c.check({"x": 1}) is True  # Not fully assigned

    def test_type_inference(self):
        c1 = Constraint(["x"], lambda x: x > 0)
        assert c1.type == ConstraintType.UNARY

        c2 = Constraint(["x", "y"], lambda x, y: x != y)
        assert c2.type == ConstraintType.BINARY

        c3 = Constraint(["x", "y", "z"], lambda x, y, z: True)
        assert c3.type == ConstraintType.NARY

    def test_all_different(self):
        c = all_different("a", "b", "c")
        assert c.check({"a": 1, "b": 2, "c": 3}) is True
        assert c.check({"a": 1, "b": 1, "c": 3}) is False

    def test_all_equal(self):
        c = all_equal("a", "b", "c")
        assert c.check({"a": 1, "b": 1, "c": 1}) is True
        assert c.check({"a": 1, "b": 2, "c": 1}) is False

    def test_sum_equals(self):
        c = sum_equals(["a", "b", "c"], 10)
        assert c.check({"a": 3, "b": 3, "c": 4}) is True
        assert c.check({"a": 1, "b": 2, "c": 3}) is False

    def test_sum_at_most(self):
        c = sum_at_most(["a", "b"], 5)
        assert c.check({"a": 2, "b": 3}) is True
        assert c.check({"a": 3, "b": 3}) is False

    def test_product_equals(self):
        c = product_equals(["a", "b"], 12)
        assert c.check({"a": 3, "b": 4}) is True
        assert c.check({"a": 3, "b": 5}) is False

    def test_less_than(self):
        c = less_than("a", "b")
        assert c.check({"a": 1, "b": 2}) is True
        assert c.check({"a": 2, "b": 1}) is False

    def test_greater_than(self):
        c = greater_than("a", "b")
        assert c.check({"a": 3, "b": 1}) is True
        assert c.check({"a": 1, "b": 3}) is False

    def test_abs_diff(self):
        c = abs_diff_equals("a", "b", 3)
        assert c.check({"a": 5, "b": 2}) is True
        assert c.check({"a": 2, "b": 5}) is True
        assert c.check({"a": 1, "b": 1}) is False

    def test_implies(self):
        c = implies("a", 1, "b", 2)
        assert c.check({"a": 1, "b": 2}) is True
        assert c.check({"a": 1, "b": 3}) is False
        assert c.check({"a": 2, "b": 5}) is True  # Antecedent false

    def test_is_fully_assigned(self):
        c = Constraint(["x", "y", "z"], lambda x, y, z: True)
        assert c.is_fully_assigned({"x": 1, "y": 2, "z": 3}) is True
        assert c.is_fully_assigned({"x": 1, "y": 2}) is False

    def test_custom_name(self):
        c = Constraint(["x"], lambda x: True, name="MyConstraint")
        assert c.name == "MyConstraint"


# --- CSP tests ---

class TestCSP:
    def test_create(self):
        csp = CSP("test")
        assert csp.name == "test"
        assert csp.num_variables == 0
        assert csp.num_constraints == 0

    def test_add_variable(self):
        csp = CSP()
        csp.add_variable(Variable("x", [1, 2, 3]))
        assert csp.num_variables == 1
        assert "x" in csp.variables

    def test_add_duplicate_variable(self):
        csp = CSP()
        csp.add_variable(Variable("x", [1]))
        with pytest.raises(ValueError):
            csp.add_variable(Variable("x", [2]))

    def test_add_constraint(self):
        csp = CSP()
        csp.add_variable(Variable("x", [1, 2]))
        csp.add_variable(Variable("y", [1, 2]))
        csp.add_constraint(not_equal("x", "y"))
        assert csp.num_constraints == 1

    def test_add_constraint_missing_var(self):
        csp = CSP()
        csp.add_variable(Variable("x", [1]))
        with pytest.raises(ValueError):
            csp.add_constraint(not_equal("x", "z"))

    def test_neighbors(self):
        csp = CSP()
        csp.add_variable(Variable("x", [1, 2]))
        csp.add_variable(Variable("y", [1, 2]))
        csp.add_variable(Variable("z", [1, 2]))
        csp.add_constraint(not_equal("x", "y"))
        assert "y" in csp.get_neighbors("x")
        assert "x" in csp.get_neighbors("y")
        assert "z" not in csp.get_neighbors("x")

    def test_is_consistent(self):
        csp = CSP()
        csp.add_variable(Variable("x", [1, 2]))
        csp.add_variable(Variable("y", [1, 2]))
        csp.add_constraint(not_equal("x", "y"))
        assert csp.is_consistent({"x": 1, "y": 2}) is True
        assert csp.is_consistent({"x": 1, "y": 1}) is False

    def test_is_complete(self):
        csp = CSP()
        csp.add_variable(Variable("x", [1]))
        csp.add_variable(Variable("y", [1]))
        assert csp.is_complete({"x": 1, "y": 1}) is True
        assert csp.is_complete({"x": 1}) is False

    def test_is_solution(self):
        csp = CSP()
        csp.add_variable(Variable("x", [1, 2]))
        csp.add_variable(Variable("y", [1, 2]))
        csp.add_constraint(not_equal("x", "y"))
        assert csp.is_solution({"x": 1, "y": 2}) is True
        assert csp.is_solution({"x": 1, "y": 1}) is False
        assert csp.is_solution({"x": 1}) is False

    def test_unassigned_variables(self):
        csp = CSP()
        csp.add_variable(Variable("x", [1]))
        csp.add_variable(Variable("y", [1]))
        csp.add_variable(Variable("z", [1]))
        assert csp.unassigned_variables({"x": 1}) == ["y", "z"]

    def test_domain_sizes(self):
        csp = CSP()
        csp.add_variable(Variable("x", [1, 2, 3]))
        csp.add_variable(Variable("y", [1, 2]))
        sizes = csp.domain_sizes
        assert sizes["x"] == 3
        assert sizes["y"] == 2

    def test_total_search_space(self):
        csp = CSP()
        csp.add_variable(Variable("x", [1, 2, 3]))
        csp.add_variable(Variable("y", [1, 2]))
        assert csp.total_search_space == 6

    def test_constraint_density(self):
        csp = CSP()
        csp.add_variables(Variable("x", [1, 2]), Variable("y", [1, 2]))
        assert csp.constraint_density == 0.0
        csp.add_constraint(not_equal("x", "y"))
        assert csp.constraint_density == 1.0

    def test_summary(self):
        csp = CSP("Test")
        csp.add_variable(Variable("x", [1, 2]))
        s = csp.summary()
        assert "Test" in s
        assert "Variables: 1" in s

    def test_copy(self):
        csp = CSP("original")
        csp.add_variable(Variable("x", [1, 2, 3]))
        csp.add_variable(Variable("y", [1, 2, 3]))
        csp.add_constraint(not_equal("x", "y"))

        csp2 = csp.copy()
        csp2.variables["x"].domain.remove(1)
        assert 1 in csp.variables["x"].domain

    def test_get_binary_constraints(self):
        csp = CSP()
        csp.add_variable(Variable("x", [1, 2]))
        csp.add_variable(Variable("y", [1, 2]))
        csp.add_variable(Variable("z", [1, 2]))
        c1 = not_equal("x", "y")
        c2 = not_equal("x", "z")
        csp.add_constraints(c1, c2)
        xy = csp.get_binary_constraints("x", "y")
        assert len(xy) == 1
        xz = csp.get_binary_constraints("x", "z")
        assert len(xz) == 1

    def test_add_variables_batch(self):
        csp = CSP()
        csp.add_variables(
            Variable("a", [1]),
            Variable("b", [2]),
            Variable("c", [3]),
        )
        assert csp.num_variables == 3

    def test_add_constraints_batch(self):
        csp = CSP()
        csp.add_variables(Variable("a", [1, 2]), Variable("b", [1, 2]), Variable("c", [1, 2]))
        csp.add_constraints(
            not_equal("a", "b"),
            not_equal("b", "c"),
        )
        assert csp.num_constraints == 2
