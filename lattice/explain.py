"""
Explanation engine for CSP solving.

Generates human-readable explanations of why values were eliminated
from domains during constraint propagation and search.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from lattice.propagation import Elimination


class ExplanationFormatter:
    """
    Formats propagation explanations into human-readable text.
    """

    def __init__(self, verbose: bool = False):
        self.verbose = verbose

    def format_eliminations(self, eliminations: List[Elimination]) -> str:
        """Format a list of eliminations as a narrative."""
        if not eliminations:
            return "No deductions were needed."

        lines = []
        # Group by variable
        by_var: Dict[str, List[Elimination]] = {}
        for e in eliminations:
            by_var.setdefault(e.variable, []).append(e)

        for var_name, elims in sorted(by_var.items()):
            if self.verbose:
                lines.append(f"\nVariable {var_name}:")
                for e in elims:
                    lines.append(f"  - Eliminated {e.value}: {e.reason}")
                    if e.constraint:
                        lines.append(f"    (via constraint: {e.constraint})")
            else:
                values = [str(e.value) for e in elims]
                reasons = set(e.reason for e in elims)
                lines.append(
                    f"  {var_name}: removed {{{', '.join(values)}}} "
                    f"({'; '.join(reasons)})"
                )

        return "\n".join(lines)

    def format_step_by_step(self, eliminations: List[Elimination]) -> List[str]:
        """Format eliminations as a numbered step-by-step guide."""
        steps = []
        for i, e in enumerate(eliminations, 1):
            step = f"Step {i}: Remove {e.value} from {e.variable}"
            if e.reason:
                step += f" because {e.reason}"
            if e.constraint:
                step += f" [constraint: {e.constraint}]"
            steps.append(step)
        return steps

    def format_summary(self, eliminations: List[Elimination]) -> str:
        """Format a brief summary of the deductions."""
        if not eliminations:
            return "No deductions were made."

        vars_affected = len(set(e.variable for e in eliminations))
        total_elims = len(eliminations)

        # Count by reason type
        by_reason: Dict[str, int] = {}
        for e in eliminations:
            key = e.constraint or "unknown"
            by_reason[key] = by_reason.get(key, 0) + 1

        lines = [
            f"Deduction summary:",
            f"  Total eliminations: {total_elims}",
            f"  Variables affected: {vars_affected}",
            f"  By technique:",
        ]
        for reason, count in sorted(by_reason.items(), key=lambda x: -x[1]):
            lines.append(f"    {reason}: {count} eliminations")

        return "\n".join(lines)


class SolveNarrator:
    """
    Narrates the entire solving process with step-by-step explanations.
    """

    def __init__(self, formatter: Optional[ExplanationFormatter] = None):
        self.formatter = formatter or ExplanationFormatter(verbose=True)
        self._narrative: List[str] = []

    def narrate_initial_propagation(self, eliminations: List[Elimination]) -> None:
        self._narrative.append("=== Initial Constraint Propagation ===")
        if eliminations:
            self._narrative.append(self.formatter.format_eliminations(eliminations))
        else:
            self._narrative.append("No values could be eliminated initially.")

    def narrate_assignment(self, var_name: str, value: Any) -> None:
        self._narrative.append(f"\n--- Trying {var_name} = {value} ---")

    def narrate_propagation(self, var_name: str, eliminations: List[Elimination]) -> None:
        if eliminations:
            self._narrative.append(f"Propagating {var_name}:")
            self._narrative.append(self.formatter.format_eliminations(eliminations))

    def narrate_backtrack(self, var_name: str, value: Any, reason: str = "") -> None:
        msg = f"Backtracking from {var_name} = {value}"
        if reason:
            msg += f" ({reason})"
        self._narrative.append(msg)

    def narrate_solution(self, assignment: Dict[str, Any]) -> None:
        self._narrative.append("\n=== Solution Found! ===")

    def narrate_failure(self) -> None:
        self._narrative.append("\n=== No Solution Exists ===")

    def get_narrative(self) -> str:
        return "\n".join(self._narrative)

    def clear(self) -> None:
        self._narrative.clear()
