"""
N-Queens puzzle solver.

Place N queens on an NxN chessboard such that no two queens threaten each other.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Any, Tuple

from lattice.core import CSP, Constraint, Variable, not_equal, abs_diff_equals
from lattice.solver import Solver, SolverConfig, SolverResult


class NQueens:
    """
    N-Queens problem: place N non-attacking queens on an NxN board.

    Variables: one per row, representing the column of the queen in that row.
    """

    def __init__(self, n: int = 8):
        if n < 1:
            raise ValueError("N must be at least 1")
        self.n = n

    def to_csp(self) -> CSP:
        """Convert to a CSP."""
        csp = CSP(f"{self.n}-Queens")

        # One variable per row: Q_i = column of queen in row i
        for i in range(self.n):
            csp.add_variable(Variable(f"Q{i}", range(self.n), row=i))

        # No two queens in the same column
        for i in range(self.n):
            for j in range(i + 1, self.n):
                csp.add_constraint(not_equal(f"Q{i}", f"Q{j}", name=f"col_{i}_{j}"))

        # No two queens on the same diagonal
        for i in range(self.n):
            for j in range(i + 1, self.n):
                diff = j - i
                csp.add_constraint(Constraint(
                    [f"Q{i}", f"Q{j}"],
                    lambda a, b, d=diff: abs(a - b) != d,
                    name=f"diag_{i}_{j}",
                ))

        return csp

    def solve(self, config: Optional[SolverConfig] = None) -> Optional[List[int]]:
        """Solve and return column positions, or None if unsolvable."""
        csp = self.to_csp()
        solver = Solver(config)
        result = solver.solve(csp)
        if result.solved:
            return [result.solution[f"Q{i}"] for i in range(self.n)]
        return None

    def solve_all(self, config: Optional[SolverConfig] = None) -> List[List[int]]:
        """Find all solutions."""
        if config is None:
            config = SolverConfig(max_solutions=0)
        else:
            config.max_solutions = 0
        csp = self.to_csp()
        solver = Solver(config)
        result = solver.solve(csp)
        solutions = []
        for sol in result.all_solutions:
            solutions.append([sol[f"Q{i}"] for i in range(self.n)])
        return solutions

    def solve_full(self, config: Optional[SolverConfig] = None) -> SolverResult:
        """Solve and return the full result with statistics."""
        csp = self.to_csp()
        solver = Solver(config)
        return solver.solve(csp)

    def format_solution(self, queens: List[int]) -> str:
        """Format a solution as a board string."""
        lines = []
        for row in range(self.n):
            line = ""
            for col in range(self.n):
                if queens[row] == col:
                    line += " Q"
                else:
                    line += " ."
            lines.append(line)
        return "\n".join(lines)

    @staticmethod
    def known_solution_counts() -> Dict[int, int]:
        """Known number of solutions for small N values."""
        return {
            1: 1, 2: 0, 3: 0, 4: 2, 5: 10, 6: 4, 7: 40, 8: 92,
            9: 352, 10: 724, 11: 2680, 12: 14200,
        }
