"""
KenKen puzzle solver.

A KenKen puzzle is an NxN grid where:
- Each row and column contains digits 1..N exactly once
- The grid is divided into "cages" with a target number and operation (+, -, *, /)
- The numbers in each cage must produce the target using the operation
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple, Any
from enum import Enum

from lattice.core import CSP, Constraint, Variable, all_different, all_different_pairwise, sum_equals, product_equals
from lattice.solver import Solver, SolverConfig, SolverResult


class Operation(Enum):
    ADD = "+"
    SUBTRACT = "-"
    MULTIPLY = "*"
    DIVIDE = "/"
    NONE = "="  # Single cell, value is given


class Cage:
    """A group of cells with a target and operation."""
    def __init__(self, cells: List[Tuple[int, int]], target: int, operation: Operation):
        self.cells = cells
        self.target = target
        self.operation = operation

    def __repr__(self) -> str:
        return f"Cage({self.cells}, {self.target}{self.operation.value})"


class KenKen:
    """
    KenKen puzzle representation and solver.
    """

    def __init__(self, size: int, cages: List[Cage]):
        self.size = size
        self.cages = cages
        self._validate()

    def _validate(self) -> None:
        all_cells = set()
        for cage in self.cages:
            for cell in cage.cells:
                r, c = cell
                if not (0 <= r < self.size and 0 <= c < self.size):
                    raise ValueError(f"Cell ({r},{c}) out of bounds for size {self.size}")
                if cell in all_cells:
                    raise ValueError(f"Cell ({r},{c}) appears in multiple cages")
                all_cells.add(cell)
        expected = {(r, c) for r in range(self.size) for c in range(self.size)}
        if all_cells != expected:
            missing = expected - all_cells
            if missing:
                raise ValueError(f"Cells not in any cage: {missing}")

    def to_csp(self) -> CSP:
        """Convert to a CSP."""
        csp = CSP(f"KenKen {self.size}x{self.size}")
        domain = range(1, self.size + 1)

        # Create variables
        for r in range(self.size):
            for c in range(self.size):
                csp.add_variable(Variable(f"r{r}c{c}", domain, row=r, col=c))

        # Row constraints (pairwise for AC-3/MAC)
        for r in range(self.size):
            row_vars = [f"r{r}c{c}" for c in range(self.size)]
            csp.add_constraints(*all_different_pairwise(*row_vars, name=f"Row{r}"))

        # Column constraints
        for c in range(self.size):
            col_vars = [f"r{r}c{c}" for r in range(self.size)]
            csp.add_constraints(*all_different_pairwise(*col_vars, name=f"Col{c}"))

        # Cage constraints
        for i, cage in enumerate(self.cages):
            cage_vars = [f"r{r}c{c}" for r, c in cage.cells]

            if cage.operation == Operation.NONE:
                # Single cell with given value
                csp.add_constraint(Constraint(
                    cage_vars,
                    lambda v, t=cage.target: v == t,
                    name=f"Cage{i}_eq{cage.target}",
                ))
            elif cage.operation == Operation.ADD:
                csp.add_constraint(sum_equals(cage_vars, cage.target, name=f"Cage{i}_sum{cage.target}"))
            elif cage.operation == Operation.MULTIPLY:
                csp.add_constraint(product_equals(cage_vars, cage.target, name=f"Cage{i}_prod{cage.target}"))
            elif cage.operation == Operation.SUBTRACT:
                csp.add_constraint(Constraint(
                    cage_vars,
                    lambda a, b, t=cage.target: abs(a - b) == t,
                    name=f"Cage{i}_sub{cage.target}",
                ))
            elif cage.operation == Operation.DIVIDE:
                csp.add_constraint(Constraint(
                    cage_vars,
                    lambda a, b, t=cage.target: (a == b * t) or (b == a * t),
                    name=f"Cage{i}_div{cage.target}",
                ))

        return csp

    def solve(self, config: Optional[SolverConfig] = None) -> Optional[List[List[int]]]:
        """Solve the puzzle."""
        csp = self.to_csp()
        solver = Solver(config)
        result = solver.solve(csp)
        if result.solved:
            return self._extract_grid(result.solution)
        return None

    def solve_full(self, config: Optional[SolverConfig] = None) -> SolverResult:
        csp = self.to_csp()
        solver = Solver(config)
        return solver.solve(csp)

    def _extract_grid(self, assignment: Dict[str, Any]) -> List[List[int]]:
        grid = [[0] * self.size for _ in range(self.size)]
        for r in range(self.size):
            for c in range(self.size):
                grid[r][c] = assignment[f"r{r}c{c}"]
        return grid

    def format_solution(self, solution: List[List[int]]) -> str:
        lines = []
        for r in range(self.size):
            lines.append(" ".join(str(v) for v in solution[r]))
        return "\n".join(lines)

    @staticmethod
    def example_4x4() -> KenKen:
        """A simple 4x4 KenKen. Solution grid:
        1 2 3 4
        3 4 1 2
        4 3 2 1
        2 1 4 3
        """
        cages = [
            Cage([(0, 0), (0, 1)], 3, Operation.ADD),
            Cage([(0, 2), (0, 3)], 1, Operation.SUBTRACT),
            Cage([(1, 0), (2, 0)], 7, Operation.ADD),
            Cage([(1, 1), (1, 2)], 4, Operation.MULTIPLY),
            Cage([(1, 3), (2, 3)], 2, Operation.DIVIDE),
            Cage([(2, 1), (2, 2)], 5, Operation.ADD),
            Cage([(3, 0), (3, 1)], 3, Operation.ADD),
            Cage([(3, 2), (3, 3)], 1, Operation.SUBTRACT),
        ]
        return KenKen(4, cages)

    @staticmethod
    def example_6x6() -> KenKen:
        """A 6x6 KenKen puzzle."""
        cages = [
            Cage([(0, 0), (1, 0)], 11, Operation.ADD),
            Cage([(0, 1), (0, 2)], 2, Operation.DIVIDE),
            Cage([(0, 3), (0, 4)], 3, Operation.SUBTRACT),
            Cage([(0, 5), (1, 5)], 5, Operation.ADD),
            Cage([(1, 1), (1, 2), (2, 1)], 10, Operation.ADD),
            Cage([(1, 3), (2, 3)], 15, Operation.MULTIPLY),
            Cage([(1, 4), (2, 4), (2, 5)], 12, Operation.MULTIPLY),
            Cage([(2, 0), (3, 0)], 1, Operation.SUBTRACT),
            Cage([(2, 2), (3, 2)], 2, Operation.DIVIDE),
            Cage([(3, 1), (4, 1)], 7, Operation.ADD),
            Cage([(3, 3), (3, 4), (3, 5)], 13, Operation.ADD),
            Cage([(4, 0), (5, 0), (5, 1)], 5, Operation.ADD),
            Cage([(4, 2), (4, 3)], 6, Operation.MULTIPLY),
            Cage([(4, 4), (4, 5)], 1, Operation.SUBTRACT),
            Cage([(5, 2), (5, 3)], 11, Operation.ADD),
            Cage([(5, 4), (5, 5)], 7, Operation.ADD),
        ]
        return KenKen(6, cages)
