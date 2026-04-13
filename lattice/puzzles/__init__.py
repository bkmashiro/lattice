"""
Built-in puzzle types that can be solved with the Lattice CSP engine.

Each puzzle module provides:
- A function to create a CSP from puzzle input
- A formatter to display solutions
- Example puzzles for testing
"""

from lattice.puzzles.sudoku import Sudoku
from lattice.puzzles.nqueens import NQueens
from lattice.puzzles.kenken import KenKen
from lattice.puzzles.futoshiki import Futoshiki
from lattice.puzzles.cryptarithmetic import Cryptarithmetic
from lattice.puzzles.nonogram import Nonogram
from lattice.puzzles.graph_coloring import GraphColoring
from lattice.puzzles.magic_square import MagicSquare
from lattice.puzzles.killer_sudoku import KillerSudoku

__all__ = [
    "Sudoku",
    "NQueens",
    "KenKen",
    "Futoshiki",
    "Cryptarithmetic",
    "Nonogram",
    "GraphColoring",
    "MagicSquare",
    "KillerSudoku",
]
