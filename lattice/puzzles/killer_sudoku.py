"""
Killer Sudoku puzzle solver.

Like regular Sudoku but with additional "cage" constraints:
groups of cells that must sum to a given target, with no
repeated digits within a cage.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple, Any

from lattice.core import CSP, Constraint, Variable, all_different, all_different_pairwise, sum_equals
from lattice.solver import Solver, SolverConfig, SolverResult


class KillerCage:
    """A cage in a Killer Sudoku: cells that must sum to target with no repeats."""
    def __init__(self, cells: List[Tuple[int, int]], target: int):
        self.cells = cells
        self.target = target


class KillerSudoku:
    """
    Killer Sudoku puzzle.

    Args:
        cages: List of KillerCage objects
        givens: Optional 9x9 grid with 0 for empty cells
    """

    def __init__(
        self,
        cages: List[KillerCage],
        givens: Optional[List[List[int]]] = None,
        size: int = 9,
    ):
        self.size = size
        self.box_size = int(size ** 0.5)
        self.cages = cages
        self.givens = givens or [[0] * size for _ in range(size)]

    def to_csp(self) -> CSP:
        csp = CSP(f"KillerSudoku {self.size}x{self.size}")
        domain = range(1, self.size + 1)

        # Create variables
        for r in range(self.size):
            for c in range(self.size):
                name = f"r{r}c{c}"
                if self.givens[r][c] != 0:
                    csp.add_variable(Variable(name, [self.givens[r][c]]))
                else:
                    csp.add_variable(Variable(name, domain))

        # Standard Sudoku constraints (pairwise for AC-3/MAC)
        bs = self.box_size
        for r in range(self.size):
            row_vars = [f"r{r}c{c}" for c in range(self.size)]
            csp.add_constraints(*all_different_pairwise(*row_vars, name=f"Row{r}"))

        for c in range(self.size):
            col_vars = [f"r{r}c{c}" for r in range(self.size)]
            csp.add_constraints(*all_different_pairwise(*col_vars, name=f"Col{c}"))

        for br in range(bs):
            for bc in range(bs):
                box_vars = []
                for r in range(br * bs, (br + 1) * bs):
                    for c in range(bc * bs, (bc + 1) * bs):
                        box_vars.append(f"r{r}c{c}")
                csp.add_constraints(*all_different_pairwise(*box_vars, name=f"Box{br}{bc}"))

        # Cage constraints
        for i, cage in enumerate(self.cages):
            cage_vars = [f"r{r}c{c}" for r, c in cage.cells]

            # Sum constraint
            csp.add_constraint(sum_equals(cage_vars, cage.target, name=f"CageSum{i}"))

            # No repeats within cage
            if len(cage_vars) > 1:
                csp.add_constraints(*all_different_pairwise(*cage_vars, name=f"CageDiff{i}"))

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
        bs = self.box_size
        for r in range(self.size):
            if r > 0 and r % bs == 0:
                lines.append("-" * (self.size * 2 + bs - 1))
            row_parts = []
            for bc in range(bs):
                part = " ".join(
                    str(solution[r][c]) for c in range(bc * bs, (bc + 1) * bs)
                )
                row_parts.append(part)
            lines.append(" | ".join(row_parts))
        return "\n".join(lines)

    @staticmethod
    def example_4x4() -> KillerSudoku:
        """A small 4x4 Killer Sudoku for testing. Solution:
        1 2 3 4
        3 4 1 2
        2 1 4 3
        4 3 2 1
        """
        cages = [
            KillerCage([(0, 0), (0, 1)], 3),
            KillerCage([(0, 2), (0, 3)], 7),
            KillerCage([(1, 0), (2, 0)], 5),
            KillerCage([(1, 1), (1, 2)], 5),
            KillerCage([(1, 3), (2, 3)], 5),
            KillerCage([(2, 1), (2, 2)], 5),
            KillerCage([(3, 0), (3, 1)], 7),
            KillerCage([(3, 2), (3, 3)], 3),
        ]
        return KillerSudoku(cages, size=4)
