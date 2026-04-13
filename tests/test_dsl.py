"""Tests for the DSL parser and builder."""

import pytest
from lattice.dsl import parse_csp, CSPBuilder, DSLParseError
from lattice.solver import Solver


class TestCSPBuilder:
    def test_basic_build(self):
        csp = (CSPBuilder("test")
               .var("x", [1, 2, 3])
               .var("y", [1, 2, 3])
               .not_eq("x", "y")
               .build())
        assert csp.num_variables == 2
        assert csp.num_constraints == 1

    def test_var_from_range(self):
        csp = CSPBuilder().var("x", range(1, 10)).build()
        assert len(csp.variables["x"].domain) == 9

    def test_multiple_vars(self):
        csp = CSPBuilder().vars(["a", "b", "c"], [1, 2, 3]).build()
        assert csp.num_variables == 3

    def test_var_grid(self):
        csp = CSPBuilder().var_grid(3, 3, [1, 2, 3]).build()
        assert csp.num_variables == 9
        assert "r0c0" in csp.variables

    def test_var_grid_custom_naming(self):
        csp = CSPBuilder().var_grid(2, 2, [1], name_fn=lambda r, c: f"cell_{r}_{c}").build()
        assert "cell_0_0" in csp.variables

    def test_all_diff(self):
        csp = (CSPBuilder()
               .var("a", [1, 2, 3])
               .var("b", [1, 2, 3])
               .var("c", [1, 2, 3])
               .all_diff("a", "b", "c")
               .build())
        result = Solver().solve(csp)
        assert result.solved
        assert len(set(result.solution.values())) == 3

    def test_all_eq(self):
        csp = (CSPBuilder()
               .var("a", [1, 2])
               .var("b", [1, 2])
               .all_eq("a", "b")
               .build())
        result = Solver().solve(csp)
        assert result.solved
        assert result.solution["a"] == result.solution["b"]

    def test_lt_gt(self):
        csp = (CSPBuilder()
               .var("x", [1, 2, 3, 4])
               .var("y", [1, 2, 3, 4])
               .lt("x", "y")
               .build())
        result = Solver().solve(csp)
        assert result.solution["x"] < result.solution["y"]

    def test_sum_eq(self):
        csp = (CSPBuilder()
               .var("a", [1, 2, 3])
               .var("b", [1, 2, 3])
               .sum_eq(["a", "b"], 4)
               .build())
        result = Solver().solve(csp)
        assert result.solution["a"] + result.solution["b"] == 4

    def test_prod_eq(self):
        csp = (CSPBuilder()
               .var("a", [1, 2, 3, 4, 5, 6])
               .var("b", [1, 2, 3, 4, 5, 6])
               .prod_eq(["a", "b"], 6)
               .build())
        result = Solver().solve(csp)
        assert result.solution["a"] * result.solution["b"] == 6

    def test_abs_diff(self):
        csp = (CSPBuilder()
               .var("a", [1, 2, 3, 4, 5])
               .var("b", [1, 2, 3, 4, 5])
               .abs_diff("a", "b", 3)
               .build())
        result = Solver().solve(csp)
        assert abs(result.solution["a"] - result.solution["b"]) == 3

    def test_fixed(self):
        csp = (CSPBuilder()
               .var("x", [1, 2, 3])
               .fixed("x", 2)
               .build())
        assert len(csp.variables["x"].domain) == 1
        result = Solver().solve(csp)
        assert result.solution["x"] == 2

    def test_fixed_nonexistent(self):
        with pytest.raises(ValueError):
            CSPBuilder().fixed("x", 1)

    def test_duplicate_var(self):
        with pytest.raises(ValueError):
            CSPBuilder().var("x", [1]).var("x", [2])

    def test_custom_constraint(self):
        csp = (CSPBuilder()
               .var("x", [1, 2, 3, 4])
               .var("y", [1, 2, 3, 4])
               .constraint(["x", "y"], lambda x, y: x * y == 6, name="xy=6")
               .build())
        result = Solver().solve(csp)
        assert result.solution["x"] * result.solution["y"] == 6

    def test_chain_fluency(self):
        """Test that all builder methods return self for chaining."""
        b = CSPBuilder("test")
        result = b.var("a", [1, 2]).var("b", [1, 2]).var("c", [1, 2])
        assert result is b


class TestDSLParser:
    def test_parse_range_domain(self):
        text = """
        variables:
            x: 1..5
        constraints:
        """
        csp = parse_csp(text)
        assert csp.num_variables == 1
        assert len(csp.variables["x"].domain) == 5

    def test_parse_set_domain(self):
        text = """
        variables:
            x: {1, 3, 5, 7}
        constraints:
        """
        csp = parse_csp(text)
        assert len(csp.variables["x"].domain) == 4

    def test_parse_string_domain(self):
        text = """
        variables:
            color: {red, green, blue}
        constraints:
        """
        csp = parse_csp(text)
        assert "red" in csp.variables["color"].domain

    def test_parse_not_equal(self):
        text = """
        variables:
            x: 1..3
            y: 1..3
        constraints:
            x != y
        """
        csp = parse_csp(text)
        assert csp.num_constraints == 1

    def test_parse_less_than(self):
        text = """
        variables:
            x: 1..5
            y: 1..5
        constraints:
            x < y
        """
        csp = parse_csp(text)
        result = Solver().solve(csp)
        assert result.solution["x"] < result.solution["y"]

    def test_parse_greater_than(self):
        text = """
        variables:
            x: 1..5
            y: 1..5
        constraints:
            x > y
        """
        csp = parse_csp(text)
        result = Solver().solve(csp)
        assert result.solution["x"] > result.solution["y"]

    def test_parse_all_different(self):
        text = """
        variables:
            a: 1..3
            b: 1..3
            c: 1..3
        constraints:
            all_different(a, b, c)
        """
        csp = parse_csp(text)
        result = Solver().solve(csp)
        assert len(set(result.solution.values())) == 3

    def test_parse_all_equal(self):
        text = """
        variables:
            a: 1..3
            b: 1..3
        constraints:
            all_equal(a, b)
        """
        csp = parse_csp(text)
        result = Solver().solve(csp)
        assert result.solution["a"] == result.solution["b"]

    def test_parse_sum(self):
        text = """
        variables:
            x: 1..5
            y: 1..5
        constraints:
            sum(x, y) == 7
        """
        csp = parse_csp(text)
        result = Solver().solve(csp)
        assert result.solution["x"] + result.solution["y"] == 7

    def test_parse_product(self):
        text = """
        variables:
            x: 1..5
            y: 1..5
        constraints:
            product(x, y) == 12
        """
        csp = parse_csp(text)
        result = Solver().solve(csp)
        assert result.solution["x"] * result.solution["y"] == 12

    def test_parse_abs_diff(self):
        text = """
        variables:
            x: 1..5
            y: 1..5
        constraints:
            |x - y| == 2
        """
        csp = parse_csp(text)
        result = Solver().solve(csp)
        assert abs(result.solution["x"] - result.solution["y"]) == 2

    def test_parse_comments(self):
        text = """
        # This is a comment
        variables:
            x: 1..3
        # Another comment
        constraints:
        """
        csp = parse_csp(text)
        assert csp.num_variables == 1

    def test_parse_negative_range(self):
        text = """
        variables:
            x: -3..3
        constraints:
        """
        csp = parse_csp(text)
        assert -3 in csp.variables["x"].domain
        assert 3 in csp.variables["x"].domain
        assert len(csp.variables["x"].domain) == 7

    def test_parse_error_invalid_variable(self):
        text = """
        variables:
            bad line here
        """
        with pytest.raises(DSLParseError):
            parse_csp(text)

    def test_parse_error_unknown_constraint(self):
        text = """
        variables:
            x: 1..3
        constraints:
            mystery_constraint(x)
        """
        with pytest.raises(DSLParseError):
            parse_csp(text)

    def test_parse_error_outside_section(self):
        text = "some random text"
        with pytest.raises(DSLParseError):
            parse_csp(text)

    def test_full_problem(self):
        text = """
        # A simple CSP
        variables:
            x: 1..4
            y: 1..4
            z: 1..4
        constraints:
            all_different(x, y, z)
            x < y
            sum(x, y, z) == 9
        """
        csp = parse_csp(text)
        result = Solver().solve(csp)
        assert result.solved
        s = result.solution
        assert len({s["x"], s["y"], s["z"]}) == 3
        assert s["x"] < s["y"]
        assert s["x"] + s["y"] + s["z"] == 9
