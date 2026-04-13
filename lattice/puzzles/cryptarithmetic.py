"""
Cryptarithmetic puzzle solver.

Solve puzzles like SEND + MORE = MONEY where each letter represents
a unique digit 0-9, and leading digits cannot be zero.
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional, Any

from lattice.core import CSP, Constraint, Variable, all_different
from lattice.solver import Solver, SolverConfig, SolverResult


class Cryptarithmetic:
    """
    Cryptarithmetic puzzle solver.

    Input: A string equation like "SEND + MORE = MONEY"
    Supports: +, -, * operators
    """

    def __init__(self, equation: str):
        self.equation = equation.strip().upper()
        self._parse()

    def _parse(self) -> None:
        """Parse the equation into operands and result."""
        # Split on =
        parts = self.equation.split("=")
        if len(parts) != 2:
            raise ValueError("Equation must have exactly one '='")

        left = parts[0].strip()
        self.result_word = re.findall(r"[A-Z]+", parts[1].strip())
        if len(self.result_word) != 1:
            raise ValueError("Right side must be a single word")
        self.result_word = self.result_word[0]

        # Parse left side for words and operators
        tokens = re.findall(r"[A-Z]+|[+\-*]", left)
        self.operands = []
        self.operators = []
        for token in tokens:
            if token in "+-*":
                self.operators.append(token)
            else:
                self.operands.append(token)

        if len(self.operands) < 2:
            raise ValueError("Need at least 2 operands")
        if len(self.operators) != len(self.operands) - 1:
            raise ValueError("Operator/operand count mismatch")

        # Extract all unique letters
        all_words = self.operands + [self.result_word]
        self.letters = sorted(set("".join(all_words)))
        self.leading_letters = set(w[0] for w in all_words)

    def to_csp(self) -> CSP:
        csp = CSP(f"Cryptarithmetic: {self.equation}")

        # One variable per letter, domain 0-9
        for letter in self.letters:
            if letter in self.leading_letters:
                csp.add_variable(Variable(letter, range(1, 10)))
            else:
                csp.add_variable(Variable(letter, range(0, 10)))

        # All letters must be different
        csp.add_constraint(all_different(*self.letters, name="AllDiffLetters"))

        # Arithmetic constraint
        def check_equation(*values):
            assignment = dict(zip(self.letters, values))
            left_val = self._word_value(self.operands[0], assignment)
            for i, op in enumerate(self.operators):
                right_val = self._word_value(self.operands[i + 1], assignment)
                if op == "+":
                    left_val += right_val
                elif op == "-":
                    left_val -= right_val
                elif op == "*":
                    left_val *= right_val
            result_val = self._word_value(self.result_word, assignment)
            return left_val == result_val

        csp.add_constraint(Constraint(
            self.letters,
            check_equation,
            name="Equation",
        ))

        return csp

    @staticmethod
    def _word_value(word: str, assignment: Dict[str, int]) -> int:
        """Convert a word to its numeric value given letter assignments."""
        result = 0
        for letter in word:
            result = result * 10 + assignment[letter]
        return result

    def solve(self, config: Optional[SolverConfig] = None) -> Optional[Dict[str, int]]:
        """Solve and return letter-to-digit mapping, or None."""
        csp = self.to_csp()
        solver = Solver(config)
        result = solver.solve(csp)
        if result.solved:
            return result.solution
        return None

    def solve_full(self, config: Optional[SolverConfig] = None) -> SolverResult:
        csp = self.to_csp()
        solver = Solver(config)
        return solver.solve(csp)

    def format_solution(self, assignment: Dict[str, int]) -> str:
        """Format the solution showing the equation with digits."""
        lines = []
        lines.append(f"  {self.equation}")
        lines.append(f"  Letter mapping:")
        for letter in sorted(assignment.keys()):
            lines.append(f"    {letter} = {assignment[letter]}")

        # Show numeric equation
        nums = []
        for word in self.operands:
            nums.append(str(self._word_value(word, assignment)))
        result_num = str(self._word_value(self.result_word, assignment))

        left = f" {self.operators[0]} ".join(nums) if self.operators else nums[0]
        lines.append(f"  {left} = {result_num}")
        return "\n".join(lines)

    @staticmethod
    def example_send_more_money() -> Cryptarithmetic:
        return Cryptarithmetic("SEND + MORE = MONEY")

    @staticmethod
    def example_eat_that_apple() -> Cryptarithmetic:
        return Cryptarithmetic("EAT + THAT = APPLE")

    @staticmethod
    def example_two_two_four() -> Cryptarithmetic:
        return Cryptarithmetic("TWO + TWO = FOUR")
