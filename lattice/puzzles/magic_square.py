"""
Magic Square solver.

An NxN grid filled with distinct integers 1..N^2 such that every row,
column, and both main diagonals sum to the same magic constant.

The magic constant for size N is: N * (N^2 + 1) / 2
"""

from __future__ import annotations

from typing import Dict, List, Optional, Any

from lattice.core import CSP, Variable, all_different, sum_equals
from lattice.solver import Solver, SolverConfig, SolverResult


class MagicSquare:
    """
    Magic Square puzzle.

    Args:
        size: Grid dimension
        givens: Optional dict mapping (row, col) to pre-filled values
    """

    def __init__(self, size: int, givens: Optional[Dict[tuple, int]] = None):
        if size < 3:
            raise ValueError("Magic squares must be at least 3x3")
        self.size = size
        self.givens = givens or {}
        self.magic_constant = size * (size * size + 1) // 2

    def to_csp(self) -> CSP:
        csp = CSP(f"MagicSquare {self.size}x{self.size}")
        domain = range(1, self.size * self.size + 1)

        # Create variables
        for r in range(self.size):
            for c in range(self.size):
                name = f"m{r}{c}"
                if (r, c) in self.givens:
                    csp.add_variable(Variable(name, [self.givens[(r, c)]]))
                else:
                    csp.add_variable(Variable(name, domain))

        # All different
        all_vars = [f"m{r}{c}" for r in range(self.size) for c in range(self.size)]
        csp.add_constraint(all_different(*all_vars, name="AllDiff"))

        # Row sums
        for r in range(self.size):
            row_vars = [f"m{r}{c}" for c in range(self.size)]
            csp.add_constraint(sum_equals(row_vars, self.magic_constant, name=f"Row{r}Sum"))

        # Column sums
        for c in range(self.size):
            col_vars = [f"m{r}{c}" for r in range(self.size)]
            csp.add_constraint(sum_equals(col_vars, self.magic_constant, name=f"Col{c}Sum"))

        # Main diagonal
        diag1 = [f"m{i}{i}" for i in range(self.size)]
        csp.add_constraint(sum_equals(diag1, self.magic_constant, name="Diag1Sum"))

        # Anti-diagonal
        diag2 = [f"m{i}{self.size-1-i}" for i in range(self.size)]
        csp.add_constraint(sum_equals(diag2, self.magic_constant, name="Diag2Sum"))

        return csp

    def solve(self, config: Optional[SolverConfig] = None) -> Optional[List[List[int]]]:
        if config is None:
            config = SolverConfig(time_limit=30.0)
        csp = self.to_csp()
        solver = Solver(config)
        result = solver.solve(csp)
        if result.solved:
            return self._extract_grid(result.solution)
        return None

    def solve_full(self, config: Optional[SolverConfig] = None) -> SolverResult:
        if config is None:
            config = SolverConfig(time_limit=30.0)
        csp = self.to_csp()
        solver = Solver(config)
        return solver.solve(csp)

    def _extract_grid(self, assignment: Dict[str, Any]) -> List[List[int]]:
        grid = [[0] * self.size for _ in range(self.size)]
        for r in range(self.size):
            for c in range(self.size):
                grid[r][c] = assignment[f"m{r}{c}"]
        return grid

    def format_solution(self, solution: List[List[int]]) -> str:
        width = len(str(self.size * self.size)) + 1
        lines = [f"Magic Square (constant = {self.magic_constant}):"]
        for r in range(self.size):
            line = " ".join(str(v).rjust(width) for v in solution[r])
            lines.append(line)
        return "\n".join(lines)

    def verify_solution(self, solution: List[List[int]]) -> bool:
        """Verify that a solution is a valid magic square."""
        n = self.size
        mc = self.magic_constant

        # All values present
        vals = sorted(solution[r][c] for r in range(n) for c in range(n))
        if vals != list(range(1, n * n + 1)):
            return False

        # Row sums
        for r in range(n):
            if sum(solution[r]) != mc:
                return False

        # Column sums
        for c in range(n):
            if sum(solution[r][c] for r in range(n)) != mc:
                return False

        # Diagonals
        if sum(solution[i][i] for i in range(n)) != mc:
            return False
        if sum(solution[i][n - 1 - i] for i in range(n)) != mc:
            return False

        return True

    @staticmethod
    def example_3x3() -> MagicSquare:
        """3x3 magic square with a few givens to speed up search."""
        return MagicSquare(3, givens={(0, 0): 2, (1, 1): 5})
