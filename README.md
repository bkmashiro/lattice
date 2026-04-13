# Lattice

> General-purpose constraint satisfaction problem (CSP) solver with AC-3 propagation and built-in puzzle solvers

![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)
![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)

## What is this?

Lattice is a CSP solver engine that combines backtracking search with constraint propagation to efficiently solve combinatorial problems. It implements AC-3 arc consistency, MAC (Maintaining Arc Consistency), forward checking, and generalized arc consistency (GAC) for n-ary constraints, along with the MRV (Minimum Remaining Values) variable ordering heuristic and degree-based tiebreaking. Together, these techniques prune the search space dramatically -- a hard Sudoku that would require millions of brute-force checks solves in milliseconds.

The library provides a clean core API for defining arbitrary CSPs (variables with finite domains, constraints as predicate functions), a fluent builder DSL, and a text-based DSL for quick problem specification. On top of this foundation, Lattice ships with dedicated solvers for 9 classic puzzles: Sudoku (4x4, 9x9, 16x16), N-Queens, graph coloring, KenKen, Killer Sudoku, Futoshiki, magic squares, nonograms, and cryptarithmetic (SEND + MORE = MONEY). Each puzzle module handles the translation from puzzle-specific representation to CSP and back.

What sets Lattice apart from a toy CSP implementation is the explanation engine. When `track_explanations` is enabled, the solver records every value elimination with the reason it was removed and the constraint responsible. This produces step-by-step deduction narratives -- useful for understanding why a puzzle has no solution, for building educational tools, or for debugging custom constraint models.

## Features

- **Backtracking search** with configurable propagation: none, forward checking, MAC (AC-3 during search), or full GAC
- **AC-3 arc consistency**: Prunes impossible values before and during search, with O(ed^3) complexity
- **Variable ordering heuristics**: MRV (fail-first), degree heuristic, MRV with degree tiebreaker, max domain, random, first-unassigned
- **Value ordering heuristics**: Ascending, descending, random, least-constraining-value
- **Rich constraint vocabulary**: `all_different`, `not_equal`, `less_than`, `greater_than`, `sum_equals`, `product_equals`, `abs_diff_equals`, `implies`, `all_equal`, `sum_at_most` -- all decomposable into binary constraints for efficient propagation
- **Domain checkpoint/restore**: Efficient backtracking with history stack and removal logging
- **Explanation engine**: Records every propagation step with human-readable reasons; formats as narratives, step-by-step guides, or summaries
- **Text DSL**: Define CSPs in a declarative text format with range (`1..9`) and set (`{a, b, c}`) domains
- **Fluent builder**: Programmatic CSP construction with method chaining, including grid variable generation
- **9 built-in puzzles**: Sudoku, N-Queens, graph coloring, KenKen, Killer Sudoku, Futoshiki, magic squares, nonograms, cryptarithmetic
- **Solution enumeration**: Find one solution, all solutions, or count solutions with configurable limits
- **Search statistics**: Nodes explored, backtracks, propagation calls, values pruned, search time, effective branching factor
- **Time and node limits**: Abort search after a deadline or node budget
- **CLI**: Interactive puzzle solving and CSP exploration from the terminal

## Installation

```bash
git clone https://github.com/bkmashiro/lattice.git
cd lattice
pip install -e .
```

No external dependencies. Lattice is pure Python.

## Quick Start

```python
from lattice import CSP, Variable, Solver, SolverConfig
from lattice.core import all_different_pairwise

# Classic: 8-Queens in 5 lines
from lattice.puzzles.nqueens import NQueens

queens = NQueens(8)
solution = queens.solve()
print(queens.format_solution(solution))
```

```
 . . . . Q . . .
 . . . . . . Q .
 . Q . . . . . .
 . . . . . Q . .
 . . Q . . . . .
 Q . . . . . . .
 . . . Q . . . .
 . . . . . . . Q
```

## Usage

### Defining a Custom CSP

```python
from lattice import CSP, Variable, Solver
from lattice.core import all_different_pairwise, sum_equals

# Map coloring: color Australia's states with 3 colors
csp = CSP("Australia")
colors = ["red", "green", "blue"]

for state in ["WA", "NT", "SA", "Q", "NSW", "V", "T"]:
    csp.add_variable(Variable(state, colors))

# Adjacent states must differ
borders = [("WA","NT"), ("WA","SA"), ("NT","SA"), ("NT","Q"),
           ("SA","Q"), ("SA","NSW"), ("SA","V"), ("Q","NSW"), ("NSW","V")]
for s1, s2 in borders:
    from lattice.core import not_equal
    csp.add_constraint(not_equal(s1, s2))

result = Solver().solve(csp)
print(result.solution)
# {'WA': 'green', 'NT': 'blue', 'SA': 'red', 'Q': 'green', 'NSW': 'blue', 'V': 'green', 'T': 'blue'}
```

### Fluent Builder

```python
from lattice.dsl import CSPBuilder

csp = (CSPBuilder("Scheduling")
    .var("meeting_A", range(9, 17))
    .var("meeting_B", range(9, 17))
    .var("meeting_C", range(9, 17))
    .all_diff("meeting_A", "meeting_B", "meeting_C")
    .constraint(["meeting_A", "meeting_B"], lambda a, b: abs(a - b) >= 2,
                name="A and B need 2h gap")
    .build())

result = Solver().solve(csp)
```

### Text DSL

```python
from lattice.dsl import parse_csp

csp = parse_csp("""
variables:
    x: 1..5
    y: 1..5
    z: 1..5

constraints:
    all_different(x, y, z)
    x < y
    sum(x, y, z) == 9
""")

result = Solver().solve(csp)
print(result.solution)  # {'x': 1, 'y': 3, 'z': 5}
```

### Solving Sudoku

```python
from lattice.puzzles.sudoku import Sudoku

puzzle = Sudoku.from_string(
    "53..7...."
    "6..195..."
    ".98....6."
    "8...6...3"
    "4..8.3..1"
    "7...2...6"
    ".6....28."
    "...419..5"
    "....8..79"
)

result = puzzle.solve_full()
print(puzzle.format_solution(puzzle.solve()))
print(result.stats.summary())
```

### Explanation Engine

See exactly why each value was eliminated:

```python
from lattice.solver import SolverConfig, PropagationLevel
from lattice.explain import ExplanationFormatter

config = SolverConfig(track_explanations=True, propagation=PropagationLevel.MAC)
result = Solver(config).solve(csp)

formatter = ExplanationFormatter(verbose=True)
print(formatter.format_eliminations(result.explanations))
# Variable x:
#   - Eliminated 4: No supporting value in y
#     (via constraint: arc(x,y))
#   - Eliminated 5: Violates unary constraint x<5
#     (via constraint: x<5)
```

### Finding All Solutions

```python
from lattice.solver import SolverConfig

config = SolverConfig(max_solutions=0)  # 0 = find all
result = Solver(config).solve(csp)
print(f"Found {result.num_solutions} solutions")

# Or with N-Queens
queens = NQueens(8)
all_solutions = queens.solve_all()
print(f"8-Queens has {len(all_solutions)} solutions")  # 92
```

### Built-in Puzzles

```python
from lattice.puzzles.nqueens import NQueens
from lattice.puzzles.sudoku import Sudoku
from lattice.puzzles.graph_coloring import GraphColoring
from lattice.puzzles.kenken import KenKen
from lattice.puzzles.magic_square import MagicSquare
from lattice.puzzles.cryptarithmetic import Cryptarithmetic
from lattice.puzzles.nonogram import Nonogram
from lattice.puzzles.futoshiki import Futoshiki
from lattice.puzzles.killer_sudoku import KillerSudoku

# Solve SEND + MORE = MONEY
crypto = Cryptarithmetic("SEND", "MORE", "MONEY")
solution = crypto.solve()
print(crypto.format_solution(solution))

# 4x4 Magic Square
ms = MagicSquare(4)
result = ms.solve_full()
print(f"Solved in {result.stats.search_time:.3f}s, {result.stats.nodes_explored} nodes")
```

## Architecture

```
lattice/
    core.py              # Variable, Domain, Constraint, CSP, constraint factories
    solver.py            # Backtracking search with configurable propagation
    propagation.py       # AC-3, MAC, forward checking, GAC, node consistency
    dsl.py               # CSPBuilder (fluent API) and text DSL parser
    explain.py           # ExplanationFormatter, SolveNarrator
    benchmark.py         # Performance benchmarking utilities
    cli.py               # Command-line interface
    heuristics/
        variable.py      # MRV, degree, MRV+degree, random, first-unassigned
        value.py         # Ascending, descending, random, LCV
    puzzles/
        sudoku.py        # 4x4, 9x9, 16x16 Sudoku
        nqueens.py       # N-Queens
        graph_coloring.py# Graph coloring (k-colorability)
        kenken.py        # KenKen arithmetic puzzles
        killer_sudoku.py # Killer Sudoku (cage constraints)
        futoshiki.py     # Futoshiki (inequality Sudoku)
        magic_square.py  # Magic squares
        nonogram.py      # Nonogram (picture logic)
        cryptarithmetic.py # Verbal arithmetic (SEND+MORE=MONEY)
```

The solver architecture follows the standard CSP pipeline: the `CSP` object holds variables (each with a `Domain` supporting checkpoint/restore for backtracking) and constraints. The `Solver` performs depth-first backtracking, calling the configured `PropagationEngine` after each assignment to prune domains. Variable and value ordering heuristics determine the search order. The `Domain` class maintains a history stack so restoring state after backtracking is O(1) amortized.

## Contributing

Contributions are welcome. Please open an issue to discuss significant changes before submitting a PR. Run the test suite with:

```bash
python -m pytest tests/ -v
```

## License

MIT
