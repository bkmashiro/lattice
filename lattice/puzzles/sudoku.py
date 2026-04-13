"""
Sudoku puzzle solver.

A 9x9 grid must be filled with digits 1-9 such that each row, column,
and 3x3 box contains all digits exactly once.

Also supports 4x4 (2x2 boxes) and 16x16 (4x4 boxes) variants.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Any

from lattice.core import CSP, Variable, all_different_pairwise
from lattice.solver import Solver, SolverConfig, SolverResult


class Sudoku:
    """
    Sudoku puzzle representation and solver.

    Input: a 2D grid where 0 represents an empty cell.
    """

    def __init__(self, grid: List[List[int]], size: int = 9):
        self.size = size
        self.box_size = int(size ** 0.5)
        if self.box_size * self.box_size != size:
            raise ValueError(f"Size {size} is not a perfect square")
        self.grid = grid
        self._validate()

    def _validate(self) -> None:
        if len(self.grid) != self.size:
            raise ValueError(f"Grid must have {self.size} rows, got {len(self.grid)}")
        for i, row in enumerate(self.grid):
            if len(row) != self.size:
                raise ValueError(f"Row {i} must have {self.size} columns, got {len(row)}")
            for val in row:
                if not (0 <= val <= self.size):
                    raise ValueError(f"Values must be 0-{self.size}, got {val}")

    def to_csp(self) -> CSP:
        """Convert to a CSP."""
        csp = CSP(f"Sudoku {self.size}x{self.size}")
        domain = range(1, self.size + 1)

        # Create variables
        for r in range(self.size):
            for c in range(self.size):
                name = f"r{r}c{c}"
                if self.grid[r][c] != 0:
                    csp.add_variable(Variable(name, [self.grid[r][c]], row=r, col=c))
                else:
                    csp.add_variable(Variable(name, domain, row=r, col=c))

        # Row constraints (pairwise for efficient AC-3/MAC propagation)
        for r in range(self.size):
            row_vars = [f"r{r}c{c}" for c in range(self.size)]
            csp.add_constraints(*all_different_pairwise(*row_vars, name=f"Row{r}"))

        # Column constraints
        for c in range(self.size):
            col_vars = [f"r{r}c{c}" for r in range(self.size)]
            csp.add_constraints(*all_different_pairwise(*col_vars, name=f"Col{c}"))

        # Box constraints
        bs = self.box_size
        for br in range(bs):
            for bc in range(bs):
                box_vars = []
                for r in range(br * bs, (br + 1) * bs):
                    for c in range(bc * bs, (bc + 1) * bs):
                        box_vars.append(f"r{r}c{c}")
                csp.add_constraints(*all_different_pairwise(*box_vars, name=f"Box{br}{bc}"))

        return csp

    def solve(self, config: Optional[SolverConfig] = None) -> Optional[List[List[int]]]:
        """Solve the puzzle and return the completed grid, or None if unsolvable."""
        csp = self.to_csp()
        solver = Solver(config)
        result = solver.solve(csp)
        if result.solved:
            return self._extract_grid(result.solution)
        return None

    def solve_full(self, config: Optional[SolverConfig] = None) -> SolverResult:
        """Solve and return the full SolverResult with statistics."""
        csp = self.to_csp()
        solver = Solver(config)
        return solver.solve(csp)

    def _extract_grid(self, assignment: Dict[str, Any]) -> List[List[int]]:
        grid = [[0] * self.size for _ in range(self.size)]
        for r in range(self.size):
            for c in range(self.size):
                grid[r][c] = assignment[f"r{r}c{c}"]
        return grid

    @staticmethod
    def from_string(s: str, size: int = 9) -> Sudoku:
        """
        Parse a Sudoku from a string.
        Supports formats:
        - 81 digits (0 for empty): "530070000600195000098000060..."
        - 9 lines of 9 digits: "530070000\n600195000\n..."
        - Dot notation: "53..7...."
        """
        # Normalize
        s = s.replace(".", "0").replace(" ", "").replace("\n", "")
        if len(s) != size * size:
            raise ValueError(f"Expected {size*size} digits, got {len(s)}")
        grid = []
        for r in range(size):
            row = []
            for c in range(size):
                row.append(int(s[r * size + c]))
            grid.append(row)
        return Sudoku(grid, size)

    def format_solution(self, solution: List[List[int]]) -> str:
        """Format a solved grid as a string."""
        lines = []
        bs = self.box_size
        width = len(str(self.size)) + 1
        separator = "+".join(["-" * (width * bs)] * bs)

        for r in range(self.size):
            if r > 0 and r % bs == 0:
                lines.append(separator)
            row_parts = []
            for bc in range(bs):
                part = " ".join(
                    str(solution[r][c]).rjust(len(str(self.size)))
                    for c in range(bc * bs, (bc + 1) * bs)
                )
                row_parts.append(part)
            lines.append(" | ".join(row_parts))
        return "\n".join(lines)

    @staticmethod
    def example_easy() -> Sudoku:
        """A known easy Sudoku puzzle."""
        return Sudoku.from_string(
            "530070000"
            "600195000"
            "098000060"
            "800060003"
            "400803001"
            "700020006"
            "060000280"
            "000419005"
            "000080079"
        )

    @staticmethod
    def example_hard() -> Sudoku:
        """A known hard Sudoku puzzle (requires backtracking)."""
        return Sudoku.from_string(
            "800000000"
            "003600000"
            "070090200"
            "050007000"
            "000045700"
            "000100030"
            "001000068"
            "008500010"
            "090000400"
        )

    @staticmethod
    def example_4x4() -> Sudoku:
        """A 4x4 Sudoku puzzle."""
        return Sudoku([
            [0, 0, 0, 2],
            [0, 0, 1, 0],
            [0, 1, 0, 0],
            [3, 0, 0, 0],
        ], size=4)
