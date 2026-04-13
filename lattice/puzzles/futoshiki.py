"""
Futoshiki puzzle solver.

An NxN grid where:
- Each row and column contains digits 1..N exactly once
- Inequality constraints between adjacent cells must be satisfied
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple, Any

from lattice.core import CSP, Variable, all_different_pairwise, less_than, greater_than
from lattice.solver import Solver, SolverConfig, SolverResult


class Futoshiki:
    """
    Futoshiki puzzle representation and solver.

    Args:
        size: Grid dimension (typically 5)
        givens: Dict mapping (row, col) to given values
        inequalities: List of ((r1,c1), (r2,c2), '<' or '>')
    """

    def __init__(
        self,
        size: int,
        givens: Optional[Dict[Tuple[int, int], int]] = None,
        inequalities: Optional[List[Tuple[Tuple[int, int], Tuple[int, int], str]]] = None,
    ):
        self.size = size
        self.givens = givens or {}
        self.inequalities = inequalities or []

    def to_csp(self) -> CSP:
        csp = CSP(f"Futoshiki {self.size}x{self.size}")
        domain = range(1, self.size + 1)

        for r in range(self.size):
            for c in range(self.size):
                name = f"r{r}c{c}"
                if (r, c) in self.givens:
                    csp.add_variable(Variable(name, [self.givens[(r, c)]]))
                else:
                    csp.add_variable(Variable(name, domain))

        # Row constraints (pairwise)
        for r in range(self.size):
            row_vars = [f"r{r}c{c}" for c in range(self.size)]
            csp.add_constraints(*all_different_pairwise(*row_vars, name=f"Row{r}"))

        # Column constraints
        for c in range(self.size):
            col_vars = [f"r{r}c{c}" for r in range(self.size)]
            csp.add_constraints(*all_different_pairwise(*col_vars, name=f"Col{c}"))

        # Inequality constraints
        for (r1, c1), (r2, c2), op in self.inequalities:
            v1 = f"r{r1}c{c1}"
            v2 = f"r{r2}c{c2}"
            if op == "<":
                csp.add_constraint(less_than(v1, v2))
            elif op == ">":
                csp.add_constraint(greater_than(v1, v2))

        return csp

    def solve(self, config: Optional[SolverConfig] = None) -> Optional[List[List[int]]]:
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
            row_str = ""
            for c in range(self.size):
                if c > 0:
                    # Check for inequality between this cell and previous
                    ineq = self._get_inequality(r, c - 1, r, c)
                    row_str += f" {ineq} "
                row_str += str(solution[r][c])
            lines.append(row_str)

            # Vertical inequalities
            if r < self.size - 1:
                vert_str = ""
                for c in range(self.size):
                    if c > 0:
                        vert_str += "   "
                    ineq = self._get_inequality(r, c, r + 1, c)
                    vert_str += ineq
                lines.append(vert_str)

        return "\n".join(lines)

    def _get_inequality(self, r1: int, c1: int, r2: int, c2: int) -> str:
        for (ar1, ac1), (ar2, ac2), op in self.inequalities:
            if ar1 == r1 and ac1 == c1 and ar2 == r2 and ac2 == c2:
                return op
            if ar1 == r2 and ac1 == c2 and ar2 == r1 and ac2 == c1:
                return ">" if op == "<" else "<"
        return " "

    @staticmethod
    def example_5x5() -> Futoshiki:
        """A 5x5 Futoshiki puzzle."""
        return Futoshiki(
            size=5,
            givens={(0, 0): 5, (2, 2): 3, (4, 4): 1},
            inequalities=[
                ((0, 1), (0, 2), "<"),
                ((1, 0), (1, 1), ">"),
                ((1, 3), (1, 4), "<"),
                ((2, 0), (3, 0), "<"),
                ((3, 2), (3, 3), ">"),
                ((3, 1), (4, 1), "<"),
            ],
        )
