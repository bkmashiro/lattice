"""
Command-line interface for the Lattice CSP solver.

Usage:
    python -m lattice sudoku "530070000600195000..."
    python -m lattice nqueens 8
    python -m lattice coloring petersen 3
    python -m lattice dsl problem.txt
    python -m lattice benchmark sudoku
"""

from __future__ import annotations

import argparse
import sys
import time
from typing import List, Optional

from lattice.solver import Solver, SolverConfig, PropagationLevel
from lattice.explain import ExplanationFormatter


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="lattice",
        description="Lattice: A General-Purpose CSP Solver",
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--explain", "-e", action="store_true", help="Show explanation trail")
    parser.add_argument(
        "--propagation", "-p",
        choices=["none", "fc", "mac"],
        default="mac",
        help="Propagation strategy",
    )
    parser.add_argument("--time-limit", "-t", type=float, default=60.0, help="Time limit in seconds")
    parser.add_argument("--all-solutions", "-a", action="store_true", help="Find all solutions")

    subparsers = parser.add_subparsers(dest="command")

    # Sudoku
    sudoku_parser = subparsers.add_parser("sudoku", help="Solve a Sudoku puzzle")
    sudoku_parser.add_argument("puzzle", nargs="?", help="81-character puzzle string (0 or . for empty)")
    sudoku_parser.add_argument("--example", choices=["easy", "hard", "4x4"], help="Use built-in example")

    # N-Queens
    nqueens_parser = subparsers.add_parser("nqueens", help="Solve N-Queens")
    nqueens_parser.add_argument("n", type=int, help="Board size")
    nqueens_parser.add_argument("--count", action="store_true", help="Count solutions only")

    # Graph Coloring
    color_parser = subparsers.add_parser("coloring", help="Solve graph coloring")
    color_parser.add_argument("graph", choices=["petersen", "australia", "cycle", "complete"],
                               help="Graph type")
    color_parser.add_argument("colors", type=int, nargs="?", default=3, help="Number of colors")
    color_parser.add_argument("--nodes", type=int, default=5, help="Nodes for cycle/complete graph")

    # KenKen
    kenken_parser = subparsers.add_parser("kenken", help="Solve a KenKen puzzle")
    kenken_parser.add_argument("--example", choices=["4x4", "6x6"], default="4x4")

    # Magic Square
    magic_parser = subparsers.add_parser("magic", help="Solve a magic square")
    magic_parser.add_argument("size", type=int, nargs="?", default=3, help="Grid size")

    # Nonogram
    nono_parser = subparsers.add_parser("nonogram", help="Solve a nonogram")
    nono_parser.add_argument("--example", choices=["heart", "cross", "arrow"], default="heart")

    # Cryptarithmetic
    crypto_parser = subparsers.add_parser("crypto", help="Solve cryptarithmetic")
    crypto_parser.add_argument("equation", nargs="?", help='Equation like "SEND + MORE = MONEY"')
    crypto_parser.add_argument("--example", choices=["send", "eat", "two"], help="Use built-in example")

    # Futoshiki
    futo_parser = subparsers.add_parser("futoshiki", help="Solve a Futoshiki puzzle")
    futo_parser.add_argument("--example", choices=["5x5"], default="5x5")

    # Killer Sudoku
    killer_parser = subparsers.add_parser("killer", help="Solve Killer Sudoku")
    killer_parser.add_argument("--example", choices=["4x4"], default="4x4")

    # DSL
    dsl_parser = subparsers.add_parser("dsl", help="Solve a CSP from DSL file")
    dsl_parser.add_argument("file", help="Path to DSL file")

    # Benchmark
    bench_parser = subparsers.add_parser("benchmark", help="Run benchmarks")
    bench_parser.add_argument("puzzle", choices=["sudoku", "nqueens", "coloring"],
                               help="Puzzle type to benchmark")

    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 0

    # Build solver config
    prop_map = {
        "none": PropagationLevel.NONE,
        "fc": PropagationLevel.FORWARD_CHECKING,
        "mac": PropagationLevel.MAC,
    }
    config = SolverConfig(
        propagation=prop_map[args.propagation],
        time_limit=args.time_limit,
        track_explanations=args.explain,
        max_solutions=0 if args.all_solutions else 1,
    )

    try:
        if args.command == "sudoku":
            return _cmd_sudoku(args, config)
        elif args.command == "nqueens":
            return _cmd_nqueens(args, config)
        elif args.command == "coloring":
            return _cmd_coloring(args, config)
        elif args.command == "kenken":
            return _cmd_kenken(args, config)
        elif args.command == "magic":
            return _cmd_magic(args, config)
        elif args.command == "nonogram":
            return _cmd_nonogram(args, config)
        elif args.command == "crypto":
            return _cmd_crypto(args, config)
        elif args.command == "futoshiki":
            return _cmd_futoshiki(args, config)
        elif args.command == "killer":
            return _cmd_killer(args, config)
        elif args.command == "dsl":
            return _cmd_dsl(args, config)
        elif args.command == "benchmark":
            return _cmd_benchmark(args)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    return 0


def _print_stats(result, explain: bool = False) -> None:
    print(f"\n{result.stats.summary()}")
    if explain and result.explanations:
        formatter = ExplanationFormatter(verbose=True)
        print(f"\n{formatter.format_summary(result.explanations)}")


def _cmd_sudoku(args, config: SolverConfig) -> int:
    from lattice.puzzles.sudoku import Sudoku

    if args.example:
        puzzle = {"easy": Sudoku.example_easy, "hard": Sudoku.example_hard, "4x4": Sudoku.example_4x4}[args.example]()
    elif args.puzzle:
        puzzle = Sudoku.from_string(args.puzzle)
    else:
        print("Provide a puzzle string or use --example", file=sys.stderr)
        return 1

    print(f"Solving {puzzle.size}x{puzzle.size} Sudoku...")
    result = puzzle.solve_full(config)
    if result.solved:
        grid = [[0] * puzzle.size for _ in range(puzzle.size)]
        for r in range(puzzle.size):
            for c in range(puzzle.size):
                grid[r][c] = result.solution[f"r{r}c{c}"]
        print(puzzle.format_solution(grid))
    else:
        print("No solution found.")
    _print_stats(result, args.explain)
    return 0 if result.solved else 1


def _cmd_nqueens(args, config: SolverConfig) -> int:
    from lattice.puzzles.nqueens import NQueens

    puzzle = NQueens(args.n)
    if args.count:
        config.max_solutions = 0
        print(f"Counting {args.n}-Queens solutions...")
        result = puzzle.solve_full(config)
        print(f"Found {result.num_solutions} solutions")
    else:
        print(f"Solving {args.n}-Queens...")
        result = puzzle.solve_full(config)
        if result.solved:
            queens = [result.solution[f"Q{i}"] for i in range(args.n)]
            print(puzzle.format_solution(queens))
        else:
            print("No solution found.")
    _print_stats(result, args.explain)
    return 0 if result.solved else 1


def _cmd_coloring(args, config: SolverConfig) -> int:
    from lattice.puzzles.graph_coloring import GraphColoring

    graph_map = {
        "petersen": lambda: GraphColoring.petersen_graph(),
        "australia": lambda: GraphColoring.australia_map(),
        "cycle": lambda: GraphColoring.cycle_graph(args.nodes, args.colors),
        "complete": lambda: GraphColoring.complete_graph(args.nodes, args.colors),
    }
    puzzle = graph_map[args.graph]()
    print(f"Solving {args.graph} graph coloring with {puzzle.num_colors} colors...")
    result = puzzle.solve_full(config)
    if result.solved:
        print(puzzle.format_solution(result.solution))
    else:
        print("No solution found (try more colors?).")
    _print_stats(result, args.explain)
    return 0 if result.solved else 1


def _cmd_kenken(args, config: SolverConfig) -> int:
    from lattice.puzzles.kenken import KenKen
    puzzle = {"4x4": KenKen.example_4x4, "6x6": KenKen.example_6x6}[args.example]()
    print(f"Solving {puzzle.size}x{puzzle.size} KenKen...")
    result = puzzle.solve_full(config)
    if result.solved:
        grid = puzzle._extract_grid(result.solution)
        print(puzzle.format_solution(grid))
    else:
        print("No solution found.")
    _print_stats(result, args.explain)
    return 0 if result.solved else 1


def _cmd_magic(args, config: SolverConfig) -> int:
    from lattice.puzzles.magic_square import MagicSquare
    puzzle = MagicSquare(args.size)
    print(f"Solving {args.size}x{args.size} magic square (constant={puzzle.magic_constant})...")
    result = puzzle.solve_full(config)
    if result.solved:
        grid = puzzle._extract_grid(result.solution)
        print(puzzle.format_solution(grid))
    else:
        print("No solution found within time limit.")
    _print_stats(result, args.explain)
    return 0 if result.solved else 1


def _cmd_nonogram(args, config: SolverConfig) -> int:
    from lattice.puzzles.nonogram import Nonogram
    puzzle = {"heart": Nonogram.example_heart, "cross": Nonogram.example_cross, "arrow": Nonogram.example_arrow}[args.example]()
    print(f"Solving {puzzle.rows}x{puzzle.cols} nonogram...")
    result = puzzle.solve_full(config)
    if result.solved:
        grid = puzzle._extract_grid(result.solution)
        print(puzzle.format_solution(grid))
    else:
        print("No solution found.")
    _print_stats(result, args.explain)
    return 0 if result.solved else 1


def _cmd_crypto(args, config: SolverConfig) -> int:
    from lattice.puzzles.cryptarithmetic import Cryptarithmetic
    if args.example:
        puzzle = {"send": Cryptarithmetic.example_send_more_money, "eat": Cryptarithmetic.example_eat_that_apple, "two": Cryptarithmetic.example_two_two_four}[args.example]()
    elif args.equation:
        puzzle = Cryptarithmetic(args.equation)
    else:
        print("Provide an equation or use --example", file=sys.stderr)
        return 1

    print(f"Solving: {puzzle.equation}")
    result = puzzle.solve_full(config)
    if result.solved:
        print(puzzle.format_solution(result.solution))
    else:
        print("No solution found.")
    _print_stats(result, args.explain)
    return 0 if result.solved else 1


def _cmd_futoshiki(args, config: SolverConfig) -> int:
    from lattice.puzzles.futoshiki import Futoshiki
    puzzle = Futoshiki.example_5x5()
    print(f"Solving {puzzle.size}x{puzzle.size} Futoshiki...")
    result = puzzle.solve_full(config)
    if result.solved:
        grid = puzzle._extract_grid(result.solution)
        print(puzzle.format_solution(grid))
    else:
        print("No solution found.")
    _print_stats(result, args.explain)
    return 0 if result.solved else 1


def _cmd_killer(args, config: SolverConfig) -> int:
    from lattice.puzzles.killer_sudoku import KillerSudoku
    puzzle = KillerSudoku.example_4x4()
    print(f"Solving Killer Sudoku...")
    result = puzzle.solve_full(config)
    if result.solved:
        grid = puzzle._extract_grid(result.solution)
        print(puzzle.format_solution(grid))
    else:
        print("No solution found.")
    _print_stats(result, args.explain)
    return 0 if result.solved else 1


def _cmd_dsl(args, config: SolverConfig) -> int:
    from lattice.dsl import parse_csp
    with open(args.file) as f:
        text = f.read()
    csp = parse_csp(text)
    print(f"Solving CSP: {csp.name}")
    print(csp.summary())
    solver = Solver(config)
    result = solver.solve(csp)
    if result.solved:
        print("\nSolution:")
        for name, value in sorted(result.solution.items()):
            print(f"  {name} = {value}")
    else:
        print("No solution found.")
    _print_stats(result, args.explain)
    return 0 if result.solved else 1


def _cmd_benchmark(args) -> int:
    from lattice.benchmark import Benchmark

    if args.puzzle == "sudoku":
        from lattice.puzzles.sudoku import Sudoku
        puzzle = Sudoku.example_hard()
        report = Benchmark.run(puzzle.to_csp)
    elif args.puzzle == "nqueens":
        from lattice.puzzles.nqueens import NQueens
        puzzle = NQueens(8)
        report = Benchmark.run(puzzle.to_csp)
    elif args.puzzle == "coloring":
        from lattice.puzzles.graph_coloring import GraphColoring
        puzzle = GraphColoring.petersen_graph()
        report = Benchmark.run(puzzle.to_csp)
    else:
        print(f"Unknown puzzle: {args.puzzle}", file=sys.stderr)
        return 1

    print(report.summary())
    if report.fastest:
        print(f"\nFastest: {report.fastest.config_name} ({report.fastest.wall_time:.4f}s)")
    return 0
