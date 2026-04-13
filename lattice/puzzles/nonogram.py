"""
Nonogram (Picross/Griddler) puzzle solver.

A grid must be filled with black (1) and white (0) cells such that
the runs of consecutive black cells in each row and column match
the given clues.
"""

from __future__ import annotations

import itertools
from typing import Dict, List, Optional, Tuple, Any

from lattice.core import CSP, Constraint, Variable
from lattice.solver import Solver, SolverConfig, SolverResult


class Nonogram:
    """
    Nonogram puzzle representation and solver.

    Args:
        rows: Number of rows
        cols: Number of columns
        row_clues: For each row, a list of run lengths
        col_clues: For each column, a list of run lengths
    """

    def __init__(
        self,
        rows: int,
        cols: int,
        row_clues: List[List[int]],
        col_clues: List[List[int]],
    ):
        self.rows = rows
        self.cols = cols
        self.row_clues = row_clues
        self.col_clues = col_clues
        self._validate()

    def _validate(self) -> None:
        if len(self.row_clues) != self.rows:
            raise ValueError(f"Expected {self.rows} row clues, got {len(self.row_clues)}")
        if len(self.col_clues) != self.cols:
            raise ValueError(f"Expected {self.cols} col clues, got {len(self.col_clues)}")

    @staticmethod
    def _generate_line_patterns(length: int, clues: List[int]) -> List[Tuple[int, ...]]:
        """
        Generate all valid binary patterns for a line of given length
        matching the given clue (run lengths).
        """
        if not clues or clues == [0]:
            return [tuple([0] * length)]

        # Minimum space needed: sum of runs + gaps between them
        min_length = sum(clues) + len(clues) - 1
        if min_length > length:
            return []

        patterns = []
        Nonogram._gen_patterns(length, clues, 0, [], patterns)
        return patterns

    @staticmethod
    def _gen_patterns(
        length: int,
        clues: List[int],
        clue_idx: int,
        current: List[int],
        results: List[Tuple[int, ...]],
    ) -> None:
        if clue_idx == len(clues):
            # Fill remaining with zeros
            pattern = current + [0] * (length - len(current))
            results.append(tuple(pattern))
            return

        clue = clues[clue_idx]
        remaining_clues = clues[clue_idx + 1:]
        remaining_needed = sum(remaining_clues) + len(remaining_clues)
        max_start = length - remaining_needed - clue

        for start in range(len(current), max_start + 1):
            # Add zeros before the block
            prefix = current + [0] * (start - len(current))
            # Add the block
            block = prefix + [1] * clue

            if clue_idx < len(clues) - 1:
                # Must have at least one zero after (gap)
                block.append(0)

            Nonogram._gen_patterns(length, clues, clue_idx + 1, block, results)

    def to_csp(self) -> CSP:
        """Convert to a CSP using a dual model."""
        csp = CSP(f"Nonogram {self.rows}x{self.cols}")

        # Create binary variables for each cell
        for r in range(self.rows):
            for c in range(self.cols):
                csp.add_variable(Variable(f"c{r}_{c}", [0, 1], row=r, col=c))

        # Row constraints: the pattern of values must match one of the valid patterns
        for r in range(self.rows):
            patterns = self._generate_line_patterns(self.cols, self.row_clues[r])
            if not patterns:
                # No valid patterns means unsolvable
                csp.add_variable(Variable(f"_fail_r{r}", []))
                continue

            row_vars = [f"c{r}_{c}" for c in range(self.cols)]
            pattern_set = set(patterns)

            csp.add_constraint(Constraint(
                row_vars,
                lambda *vals, ps=pattern_set: tuple(vals) in ps,
                name=f"RowClue{r}",
            ))

        # Column constraints
        for c in range(self.cols):
            patterns = self._generate_line_patterns(self.rows, self.col_clues[c])
            if not patterns:
                csp.add_variable(Variable(f"_fail_c{c}", []))
                continue

            col_vars = [f"c{r}_{c}" for r in range(self.rows)]
            pattern_set = set(patterns)

            csp.add_constraint(Constraint(
                col_vars,
                lambda *vals, ps=pattern_set: tuple(vals) in ps,
                name=f"ColClue{c}",
            ))

        return csp

    def solve(self, config: Optional[SolverConfig] = None) -> Optional[List[List[int]]]:
        """Solve the nonogram."""
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
        grid = [[0] * self.cols for _ in range(self.rows)]
        for r in range(self.rows):
            for c in range(self.cols):
                grid[r][c] = assignment[f"c{r}_{c}"]
        return grid

    def format_solution(self, solution: List[List[int]]) -> str:
        """Format as a visual grid."""
        lines = []
        for r in range(self.rows):
            line = ""
            for c in range(self.cols):
                line += "\u2588\u2588" if solution[r][c] == 1 else "  "
            lines.append(line)
        return "\n".join(lines)

    @staticmethod
    def example_heart() -> Nonogram:
        """A small 5x5 heart pattern."""
        return Nonogram(
            rows=5, cols=5,
            row_clues=[[1, 1], [5], [5], [3], [1]],
            col_clues=[[2], [4], [4], [4], [2]],
        )

    @staticmethod
    def example_cross() -> Nonogram:
        """A 5x5 cross/plus pattern."""
        return Nonogram(
            rows=5, cols=5,
            row_clues=[[1], [3], [5], [3], [1]],
            col_clues=[[1], [3], [5], [3], [1]],
        )

    @staticmethod
    def example_arrow() -> Nonogram:
        """A 7x7 arrow pattern."""
        return Nonogram(
            rows=7, cols=7,
            row_clues=[[1], [2], [3], [7], [3], [2], [1]],
            col_clues=[[1], [1], [1], [7], [3], [2], [1]],
        )
