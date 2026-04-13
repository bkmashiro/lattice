"""
Lattice - A General-Purpose Constraint Satisfaction Problem (CSP) Solver Engine

Lattice provides a unified framework for defining and solving constraint satisfaction
problems. It includes:

- A core CSP engine with AC-3 arc consistency and backtracking search
- Multiple variable and value ordering heuristics
- Explanation generation for constraint propagation steps
- Built-in solvers for classic puzzles (Sudoku, Nonogram, KenKen, etc.)
- A DSL for defining custom CSPs
- CLI interface for interactive solving
"""

__version__ = "1.0.0"

from lattice.core import Variable, Domain, Constraint, CSP, all_different_pairwise
from lattice.solver import Solver, SolverConfig, SolverResult
from lattice.dsl import parse_csp, CSPBuilder

__all__ = [
    "Variable",
    "Domain",
    "Constraint",
    "CSP",
    "Solver",
    "SolverConfig",
    "SolverResult",
    "parse_csp",
    "CSPBuilder",
]
