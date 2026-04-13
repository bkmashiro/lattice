"""
Graph coloring puzzle solver.

Given a graph and K colors, assign a color to each node such that
no two adjacent nodes share a color.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Set, Tuple, Any

from lattice.core import CSP, Variable, not_equal
from lattice.solver import Solver, SolverConfig, SolverResult


class GraphColoring:
    """
    Graph coloring problem.

    Args:
        nodes: List of node names
        edges: List of (node1, node2) pairs
        num_colors: Number of available colors
        color_names: Optional names for colors (defaults to integers)
    """

    def __init__(
        self,
        nodes: List[str],
        edges: List[Tuple[str, str]],
        num_colors: int,
        color_names: Optional[List[str]] = None,
    ):
        self.nodes = nodes
        self.edges = edges
        self.num_colors = num_colors
        self.color_names = color_names or [str(i) for i in range(num_colors)]
        self._validate()

    def _validate(self) -> None:
        node_set = set(self.nodes)
        for n1, n2 in self.edges:
            if n1 not in node_set:
                raise ValueError(f"Edge references unknown node: {n1}")
            if n2 not in node_set:
                raise ValueError(f"Edge references unknown node: {n2}")
        if len(self.color_names) != self.num_colors:
            raise ValueError("color_names length must match num_colors")

    def to_csp(self) -> CSP:
        csp = CSP(f"GraphColoring({len(self.nodes)} nodes, {self.num_colors} colors)")

        for node in self.nodes:
            csp.add_variable(Variable(node, self.color_names))

        for n1, n2 in self.edges:
            csp.add_constraint(not_equal(n1, n2, name=f"{n1}!={n2}"))

        return csp

    def solve(self, config: Optional[SolverConfig] = None) -> Optional[Dict[str, str]]:
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

    def chromatic_number(self, max_colors: int = 20) -> int:
        """Find the minimum number of colors needed to color the graph."""
        for k in range(1, max_colors + 1):
            gc = GraphColoring(self.nodes, self.edges, k)
            if gc.solve() is not None:
                return k
        return -1

    def format_solution(self, coloring: Dict[str, str]) -> str:
        lines = ["Graph Coloring:"]
        for node in sorted(coloring.keys()):
            lines.append(f"  {node}: {coloring[node]}")
        return "\n".join(lines)

    @staticmethod
    def petersen_graph() -> GraphColoring:
        """The Petersen graph (chromatic number 3)."""
        outer = [f"o{i}" for i in range(5)]
        inner = [f"i{i}" for i in range(5)]
        nodes = outer + inner

        edges = []
        # Outer cycle
        for i in range(5):
            edges.append((outer[i], outer[(i + 1) % 5]))
        # Inner pentagram
        for i in range(5):
            edges.append((inner[i], inner[(i + 2) % 5]))
        # Spokes
        for i in range(5):
            edges.append((outer[i], inner[i]))

        return GraphColoring(nodes, edges, 3)

    @staticmethod
    def australia_map() -> GraphColoring:
        """Australian states map coloring."""
        nodes = ["WA", "NT", "SA", "Q", "NSW", "V", "T"]
        edges = [
            ("WA", "NT"), ("WA", "SA"),
            ("NT", "SA"), ("NT", "Q"),
            ("SA", "Q"), ("SA", "NSW"), ("SA", "V"),
            ("Q", "NSW"),
            ("NSW", "V"),
        ]
        return GraphColoring(nodes, edges, 3, ["Red", "Green", "Blue"])

    @staticmethod
    def complete_graph(n: int, k: int) -> GraphColoring:
        """Complete graph K_n with k colors."""
        nodes = [f"n{i}" for i in range(n)]
        edges = [(f"n{i}", f"n{j}") for i in range(n) for j in range(i + 1, n)]
        return GraphColoring(nodes, edges, k)

    @staticmethod
    def cycle_graph(n: int, k: int = 3) -> GraphColoring:
        """Cycle graph C_n with k colors."""
        nodes = [f"n{i}" for i in range(n)]
        edges = [(f"n{i}", f"n{(i+1)%n}") for i in range(n)]
        return GraphColoring(nodes, edges, k)
