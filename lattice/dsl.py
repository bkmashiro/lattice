"""
A Domain-Specific Language (DSL) for defining Constraint Satisfaction Problems.

Provides both a programmatic builder API and a text-based parser.

Text DSL syntax:
    # Comment
    variables:
        x: 1..9
        y: {a, b, c}
        z: 1..5

    constraints:
        all_different(x, y, z)
        x != y
        x < z
        sum(x, y, z) == 15
        x + y == z
"""

from __future__ import annotations

import re
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

from lattice.core import (
    CSP,
    Constraint,
    ConstraintType,
    Domain,
    Variable,
    all_different,
    all_equal,
    less_than,
    greater_than,
    not_equal,
    sum_equals,
    product_equals,
    abs_diff_equals,
)


class CSPBuilder:
    """
    Fluent builder for constructing CSPs programmatically.

    Example:
        csp = (CSPBuilder("My Problem")
            .var("x", range(1, 10))
            .var("y", range(1, 10))
            .var("z", range(1, 10))
            .all_diff("x", "y", "z")
            .constraint(["x", "y"], lambda x, y: x + y > 5)
            .build())
    """

    def __init__(self, name: str = "CSP"):
        self._name = name
        self._variables: List[Variable] = []
        self._constraints: List[Constraint] = []
        self._var_names: Set[str] = set()

    def var(self, name: str, domain: Any, **metadata) -> CSPBuilder:
        """Add a variable with the given domain."""
        if name in self._var_names:
            raise ValueError(f"Variable '{name}' already defined")
        if isinstance(domain, range):
            domain = list(domain)
        self._variables.append(Variable(name, domain, **metadata))
        self._var_names.add(name)
        return self

    def vars(self, names: List[str], domain: Any, **metadata) -> CSPBuilder:
        """Add multiple variables with the same domain."""
        for name in names:
            self.var(name, domain, **metadata)
        return self

    def var_grid(
        self, rows: int, cols: int, domain: Any,
        name_fn: Optional[Callable[[int, int], str]] = None,
        **metadata,
    ) -> CSPBuilder:
        """Add a grid of variables."""
        if name_fn is None:
            name_fn = lambda r, c: f"r{r}c{c}"
        for r in range(rows):
            for c in range(cols):
                self.var(name_fn(r, c), domain, row=r, col=c, **metadata)
        return self

    def constraint(
        self,
        scope: List[str],
        check: Callable[..., bool],
        name: str = "",
    ) -> CSPBuilder:
        """Add a constraint."""
        self._constraints.append(Constraint(scope, check, name=name))
        return self

    def all_diff(self, *var_names: str, name: str = "") -> CSPBuilder:
        """Add an all-different constraint."""
        self._constraints.append(all_different(*var_names, name=name))
        return self

    def all_eq(self, *var_names: str, name: str = "") -> CSPBuilder:
        """Add an all-equal constraint."""
        self._constraints.append(all_equal(*var_names, name=name))
        return self

    def not_eq(self, var1: str, var2: str, name: str = "") -> CSPBuilder:
        """Add a not-equal constraint."""
        self._constraints.append(not_equal(var1, var2, name=name))
        return self

    def lt(self, var1: str, var2: str, name: str = "") -> CSPBuilder:
        """Add a less-than constraint."""
        self._constraints.append(less_than(var1, var2, name=name))
        return self

    def gt(self, var1: str, var2: str, name: str = "") -> CSPBuilder:
        """Add a greater-than constraint."""
        self._constraints.append(greater_than(var1, var2, name=name))
        return self

    def sum_eq(self, var_names: List[str], target: int, name: str = "") -> CSPBuilder:
        """Add a sum-equals constraint."""
        self._constraints.append(sum_equals(var_names, target, name=name))
        return self

    def prod_eq(self, var_names: List[str], target: int, name: str = "") -> CSPBuilder:
        """Add a product-equals constraint."""
        self._constraints.append(product_equals(var_names, target, name=name))
        return self

    def abs_diff(self, var1: str, var2: str, diff: int, name: str = "") -> CSPBuilder:
        """Add an absolute-difference constraint."""
        self._constraints.append(abs_diff_equals(var1, var2, diff, name=name))
        return self

    def fixed(self, var_name: str, value: Any) -> CSPBuilder:
        """Fix a variable to a single value (pre-assignment)."""
        for v in self._variables:
            if v.name == var_name:
                v.domain = Domain([value])
                return self
        raise ValueError(f"Variable '{var_name}' not found")

    def build(self) -> CSP:
        """Build and return the CSP."""
        csp = CSP(self._name)
        for var in self._variables:
            csp.add_variable(var)
        for constraint in self._constraints:
            csp.add_constraint(constraint)
        return csp


# --- Text DSL Parser ---

class DSLParseError(Exception):
    """Error during DSL parsing."""
    def __init__(self, message: str, line: int = 0):
        self.line = line
        super().__init__(f"Line {line}: {message}" if line else message)


def parse_csp(text: str, name: str = "CSP") -> CSP:
    """
    Parse a CSP from the text DSL format.

    Returns a CSP object.
    """
    builder = CSPBuilder(name)
    lines = text.strip().split("\n")
    section = None
    line_num = 0

    for raw_line in lines:
        line_num += 1
        line = raw_line.strip()

        # Skip comments and empty lines
        if not line or line.startswith("#"):
            continue

        # Section headers
        if line.rstrip(":") in ("variables", "constraints"):
            section = line.rstrip(":")
            continue

        if section == "variables":
            _parse_variable(builder, line, line_num)
        elif section == "constraints":
            _parse_constraint(builder, line, line_num)
        else:
            raise DSLParseError(f"Unexpected content outside section: {line}", line_num)

    return builder.build()


def _parse_variable(builder: CSPBuilder, line: str, line_num: int) -> None:
    """Parse a variable definition like 'x: 1..9' or 'y: {a, b, c}'."""
    match = re.match(r"(\w+)\s*:\s*(.+)", line)
    if not match:
        raise DSLParseError(f"Invalid variable definition: {line}", line_num)

    name = match.group(1)
    domain_str = match.group(2).strip()

    # Range syntax: 1..9
    range_match = re.match(r"(-?\d+)\.\.(-?\d+)", domain_str)
    if range_match:
        lo, hi = int(range_match.group(1)), int(range_match.group(2))
        builder.var(name, range(lo, hi + 1))
        return

    # Set syntax: {a, b, c} or {1, 2, 3}
    set_match = re.match(r"\{(.+)\}", domain_str)
    if set_match:
        elements = [e.strip() for e in set_match.group(1).split(",")]
        # Try to convert to integers
        try:
            domain = [int(e) for e in elements]
        except ValueError:
            domain = elements
        builder.var(name, domain)
        return

    raise DSLParseError(f"Invalid domain: {domain_str}", line_num)


def _parse_constraint(builder: CSPBuilder, line: str, line_num: int) -> None:
    """Parse a constraint definition."""
    # all_different(x, y, z)
    ad_match = re.match(r"all_different\((.+)\)", line)
    if ad_match:
        vars_ = [v.strip() for v in ad_match.group(1).split(",")]
        builder.all_diff(*vars_)
        return

    # all_equal(x, y, z)
    ae_match = re.match(r"all_equal\((.+)\)", line)
    if ae_match:
        vars_ = [v.strip() for v in ae_match.group(1).split(",")]
        builder.all_eq(*vars_)
        return

    # sum(x, y, z) == N
    sum_match = re.match(r"sum\((.+)\)\s*==\s*(-?\d+)", line)
    if sum_match:
        vars_ = [v.strip() for v in sum_match.group(1).split(",")]
        target = int(sum_match.group(2))
        builder.sum_eq(vars_, target)
        return

    # product(x, y, z) == N
    prod_match = re.match(r"product\((.+)\)\s*==\s*(-?\d+)", line)
    if prod_match:
        vars_ = [v.strip() for v in prod_match.group(1).split(",")]
        target = int(prod_match.group(2))
        builder.prod_eq(vars_, target)
        return

    # x != y
    neq_match = re.match(r"(\w+)\s*!=\s*(\w+)", line)
    if neq_match:
        builder.not_eq(neq_match.group(1), neq_match.group(2))
        return

    # x < y
    lt_match = re.match(r"(\w+)\s*<\s*(\w+)", line)
    if lt_match:
        builder.lt(lt_match.group(1), lt_match.group(2))
        return

    # x > y
    gt_match = re.match(r"(\w+)\s*>\s*(\w+)", line)
    if gt_match:
        builder.gt(gt_match.group(1), gt_match.group(2))
        return

    # |x - y| == N
    abs_match = re.match(r"\|(\w+)\s*-\s*(\w+)\|\s*==\s*(-?\d+)", line)
    if abs_match:
        diff = int(abs_match.group(3))
        builder.abs_diff(abs_match.group(1), abs_match.group(2), diff)
        return

    raise DSLParseError(f"Unknown constraint syntax: {line}", line_num)
