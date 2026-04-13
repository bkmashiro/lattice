"""Tests for built-in puzzle solvers."""

import pytest
from lattice.solver import SolverConfig, PropagationLevel


# --- Sudoku ---

class TestSudoku:
    def test_solve_easy(self):
        from lattice.puzzles.sudoku import Sudoku
        puzzle = Sudoku.example_easy()
        grid = puzzle.solve()
        assert grid is not None
        # Verify all rows have 1-9
        for row in grid:
            assert sorted(row) == list(range(1, 10))
        # Verify all columns
        for c in range(9):
            col = [grid[r][c] for r in range(9)]
            assert sorted(col) == list(range(1, 10))

    def test_solve_hard(self):
        from lattice.puzzles.sudoku import Sudoku
        puzzle = Sudoku.example_hard()
        grid = puzzle.solve()
        assert grid is not None
        for row in grid:
            assert sorted(row) == list(range(1, 10))

    def test_solve_4x4(self):
        from lattice.puzzles.sudoku import Sudoku
        puzzle = Sudoku.example_4x4()
        grid = puzzle.solve()
        assert grid is not None
        for row in grid:
            assert sorted(row) == [1, 2, 3, 4]

    def test_from_string_dots(self):
        from lattice.puzzles.sudoku import Sudoku
        s = "53..7...." + "." * 72
        puzzle = Sudoku.from_string(s)
        assert puzzle.grid[0][0] == 5
        assert puzzle.grid[0][2] == 0

    def test_invalid_grid_size(self):
        from lattice.puzzles.sudoku import Sudoku
        with pytest.raises(ValueError):
            Sudoku([[1, 2], [3, 4]], size=9)

    def test_invalid_value(self):
        from lattice.puzzles.sudoku import Sudoku
        grid = [[0]*9 for _ in range(9)]
        grid[0][0] = 10
        with pytest.raises(ValueError):
            Sudoku(grid)

    def test_from_string_wrong_length(self):
        from lattice.puzzles.sudoku import Sudoku
        with pytest.raises(ValueError):
            Sudoku.from_string("123")

    def test_format_solution(self):
        from lattice.puzzles.sudoku import Sudoku
        puzzle = Sudoku.example_4x4()
        grid = puzzle.solve()
        formatted = puzzle.format_solution(grid)
        assert "|" in formatted

    def test_solve_full_returns_stats(self):
        from lattice.puzzles.sudoku import Sudoku
        puzzle = Sudoku.example_easy()
        result = puzzle.solve_full()
        assert result.solved
        assert result.stats.search_time >= 0

    def test_invalid_size(self):
        from lattice.puzzles.sudoku import Sudoku
        with pytest.raises(ValueError):
            Sudoku([[0]*5]*5, size=5)


# --- N-Queens ---

class TestNQueens:
    def test_solve_4(self):
        from lattice.puzzles.nqueens import NQueens
        puzzle = NQueens(4)
        solution = puzzle.solve()
        assert solution is not None
        assert len(solution) == 4
        # No two queens in same column
        assert len(set(solution)) == 4
        # No diagonal conflicts
        for i in range(4):
            for j in range(i + 1, 4):
                assert abs(solution[i] - solution[j]) != abs(i - j)

    def test_solve_8(self):
        from lattice.puzzles.nqueens import NQueens
        puzzle = NQueens(8)
        solution = puzzle.solve()
        assert solution is not None
        assert len(set(solution)) == 8

    def test_solve_1(self):
        from lattice.puzzles.nqueens import NQueens
        puzzle = NQueens(1)
        solution = puzzle.solve()
        assert solution == [0]

    def test_count_4(self):
        from lattice.puzzles.nqueens import NQueens
        puzzle = NQueens(4)
        solutions = puzzle.solve_all()
        assert len(solutions) == 2

    def test_count_5(self):
        from lattice.puzzles.nqueens import NQueens
        puzzle = NQueens(5)
        solutions = puzzle.solve_all()
        assert len(solutions) == 10

    def test_format_solution(self):
        from lattice.puzzles.nqueens import NQueens
        puzzle = NQueens(4)
        solution = puzzle.solve()
        formatted = puzzle.format_solution(solution)
        assert "Q" in formatted
        assert "." in formatted

    def test_known_counts(self):
        from lattice.puzzles.nqueens import NQueens
        counts = NQueens.known_solution_counts()
        assert counts[4] == 2
        assert counts[8] == 92

    def test_invalid_n(self):
        from lattice.puzzles.nqueens import NQueens
        with pytest.raises(ValueError):
            NQueens(0)


# --- Graph Coloring ---

class TestGraphColoring:
    def test_australia(self):
        from lattice.puzzles.graph_coloring import GraphColoring
        puzzle = GraphColoring.australia_map()
        coloring = puzzle.solve()
        assert coloring is not None
        # Verify no adjacent same color
        for n1, n2 in puzzle.edges:
            assert coloring[n1] != coloring[n2]

    def test_petersen(self):
        from lattice.puzzles.graph_coloring import GraphColoring
        puzzle = GraphColoring.petersen_graph()
        coloring = puzzle.solve()
        assert coloring is not None

    def test_complete_graph_not_colorable(self):
        from lattice.puzzles.graph_coloring import GraphColoring
        # K4 with 3 colors is not colorable
        puzzle = GraphColoring.complete_graph(4, 3)
        coloring = puzzle.solve()
        assert coloring is None

    def test_complete_graph_colorable(self):
        from lattice.puzzles.graph_coloring import GraphColoring
        puzzle = GraphColoring.complete_graph(4, 4)
        coloring = puzzle.solve()
        assert coloring is not None

    def test_cycle_odd(self):
        from lattice.puzzles.graph_coloring import GraphColoring
        puzzle = GraphColoring.cycle_graph(5, 3)
        coloring = puzzle.solve()
        assert coloring is not None

    def test_cycle_even_2_colors(self):
        from lattice.puzzles.graph_coloring import GraphColoring
        puzzle = GraphColoring.cycle_graph(4, 2)
        coloring = puzzle.solve()
        assert coloring is not None

    def test_cycle_odd_2_colors(self):
        from lattice.puzzles.graph_coloring import GraphColoring
        puzzle = GraphColoring.cycle_graph(3, 2)
        coloring = puzzle.solve()
        assert coloring is None

    def test_invalid_edge(self):
        from lattice.puzzles.graph_coloring import GraphColoring
        with pytest.raises(ValueError):
            GraphColoring(["a", "b"], [("a", "c")], 2)

    def test_format_solution(self):
        from lattice.puzzles.graph_coloring import GraphColoring
        puzzle = GraphColoring.australia_map()
        coloring = puzzle.solve()
        formatted = puzzle.format_solution(coloring)
        assert "WA" in formatted


# --- KenKen ---

class TestKenKen:
    def test_solve_4x4(self):
        from lattice.puzzles.kenken import KenKen
        puzzle = KenKen.example_4x4()
        grid = puzzle.solve()
        assert grid is not None
        for row in grid:
            assert sorted(row) == [1, 2, 3, 4]
        for c in range(4):
            col = [grid[r][c] for r in range(4)]
            assert sorted(col) == [1, 2, 3, 4]

    def test_solve_6x6(self):
        from lattice.puzzles.kenken import KenKen
        puzzle = KenKen.example_6x6()
        grid = puzzle.solve()
        assert grid is not None
        for row in grid:
            assert sorted(row) == [1, 2, 3, 4, 5, 6]

    def test_invalid_duplicate_cell(self):
        from lattice.puzzles.kenken import KenKen, Cage, Operation
        with pytest.raises(ValueError):
            KenKen(2, [
                Cage([(0, 0), (0, 0)], 3, Operation.ADD),
                Cage([(0, 1), (1, 0)], 3, Operation.ADD),
                Cage([(1, 1)], 1, Operation.NONE),
            ])

    def test_invalid_cell_out_of_bounds(self):
        from lattice.puzzles.kenken import KenKen, Cage, Operation
        with pytest.raises(ValueError):
            KenKen(2, [Cage([(0, 0), (5, 5)], 3, Operation.ADD)])


# --- Futoshiki ---

class TestFutoshiki:
    def test_solve_5x5(self):
        from lattice.puzzles.futoshiki import Futoshiki
        puzzle = Futoshiki.example_5x5()
        grid = puzzle.solve()
        assert grid is not None
        for row in grid:
            assert sorted(row) == [1, 2, 3, 4, 5]
        assert grid[0][0] == 5

    def test_format_solution(self):
        from lattice.puzzles.futoshiki import Futoshiki
        puzzle = Futoshiki.example_5x5()
        grid = puzzle.solve()
        formatted = puzzle.format_solution(grid)
        assert "5" in formatted


# --- Cryptarithmetic ---

class TestCryptarithmetic:
    def test_send_more_money(self):
        from lattice.puzzles.cryptarithmetic import Cryptarithmetic
        puzzle = Cryptarithmetic.example_send_more_money()
        config = SolverConfig(time_limit=30.0, propagation=PropagationLevel.NONE)
        solution = puzzle.solve(config)
        assert solution is not None
        # SEND + MORE = MONEY => 9567 + 1085 = 10652
        assert solution["M"] == 1
        # Verify equation
        send = solution["S"]*1000 + solution["E"]*100 + solution["N"]*10 + solution["D"]
        more = solution["M"]*1000 + solution["O"]*100 + solution["R"]*10 + solution["E"]
        money = solution["M"]*10000 + solution["O"]*1000 + solution["N"]*100 + solution["E"]*10 + solution["Y"]
        assert send + more == money

    def test_two_two_four(self):
        from lattice.puzzles.cryptarithmetic import Cryptarithmetic
        puzzle = Cryptarithmetic.example_two_two_four()
        config = SolverConfig(time_limit=30.0, propagation=PropagationLevel.NONE)
        solution = puzzle.solve(config)
        assert solution is not None

    def test_format_solution(self):
        from lattice.puzzles.cryptarithmetic import Cryptarithmetic
        puzzle = Cryptarithmetic.example_send_more_money()
        config = SolverConfig(time_limit=30.0, propagation=PropagationLevel.NONE)
        solution = puzzle.solve(config)
        formatted = puzzle.format_solution(solution)
        assert "SEND" in formatted

    def test_invalid_equation(self):
        from lattice.puzzles.cryptarithmetic import Cryptarithmetic
        with pytest.raises(ValueError):
            Cryptarithmetic("INVALID")

    def test_parse_equation(self):
        from lattice.puzzles.cryptarithmetic import Cryptarithmetic
        p = Cryptarithmetic("AB + CD = EF")
        assert p.operands == ["AB", "CD"]
        assert p.result_word == "EF"
        assert p.operators == ["+"]


# --- Nonogram ---

class TestNonogram:
    def test_solve_heart(self):
        from lattice.puzzles.nonogram import Nonogram
        puzzle = Nonogram.example_heart()
        grid = puzzle.solve()
        assert grid is not None
        # Verify row clues
        assert grid[0] == [0, 1, 0, 1, 0]  # [1, 1]
        assert sum(grid[1]) == 5  # [5]
        assert sum(grid[4]) == 1  # [1]

    def test_solve_cross(self):
        from lattice.puzzles.nonogram import Nonogram
        puzzle = Nonogram.example_cross()
        grid = puzzle.solve()
        assert grid is not None
        assert grid[2] == [1, 1, 1, 1, 1]  # [5]

    def test_format_solution(self):
        from lattice.puzzles.nonogram import Nonogram
        puzzle = Nonogram.example_heart()
        grid = puzzle.solve()
        formatted = puzzle.format_solution(grid)
        assert len(formatted) > 0

    def test_pattern_generation(self):
        from lattice.puzzles.nonogram import Nonogram
        patterns = Nonogram._generate_line_patterns(5, [2, 1])
        assert len(patterns) > 0
        for p in patterns:
            assert len(p) == 5
            assert all(v in (0, 1) for v in p)

    def test_empty_clue(self):
        from lattice.puzzles.nonogram import Nonogram
        patterns = Nonogram._generate_line_patterns(5, [0])
        assert patterns == [(0, 0, 0, 0, 0)]

    def test_full_clue(self):
        from lattice.puzzles.nonogram import Nonogram
        patterns = Nonogram._generate_line_patterns(3, [3])
        assert patterns == [(1, 1, 1)]

    def test_impossible_clue(self):
        from lattice.puzzles.nonogram import Nonogram
        patterns = Nonogram._generate_line_patterns(3, [2, 2])
        assert patterns == []

    def test_invalid_clue_count(self):
        from lattice.puzzles.nonogram import Nonogram
        with pytest.raises(ValueError):
            Nonogram(3, 3, row_clues=[[1]], col_clues=[[1], [1], [1]])


# --- Magic Square ---

class TestMagicSquare:
    def test_solve_3x3(self):
        from lattice.puzzles.magic_square import MagicSquare
        puzzle = MagicSquare.example_3x3()
        grid = puzzle.solve()
        assert grid is not None
        assert puzzle.verify_solution(grid)

    def test_magic_constant(self):
        from lattice.puzzles.magic_square import MagicSquare
        ms = MagicSquare(3)
        assert ms.magic_constant == 15
        ms4 = MagicSquare(4)
        assert ms4.magic_constant == 34

    def test_verify_valid(self):
        from lattice.puzzles.magic_square import MagicSquare
        ms = MagicSquare(3)
        valid = [
            [2, 7, 6],
            [9, 5, 1],
            [4, 3, 8],
        ]
        assert ms.verify_solution(valid)

    def test_verify_invalid(self):
        from lattice.puzzles.magic_square import MagicSquare
        ms = MagicSquare(3)
        invalid = [
            [1, 2, 3],
            [4, 5, 6],
            [7, 8, 9],
        ]
        assert not ms.verify_solution(invalid)

    def test_invalid_size(self):
        from lattice.puzzles.magic_square import MagicSquare
        with pytest.raises(ValueError):
            MagicSquare(2)

    def test_format(self):
        from lattice.puzzles.magic_square import MagicSquare
        ms = MagicSquare(3)
        grid = ms.solve()
        if grid:
            formatted = ms.format_solution(grid)
            assert "15" in formatted


# --- Killer Sudoku ---

class TestKillerSudoku:
    def test_solve_4x4(self):
        from lattice.puzzles.killer_sudoku import KillerSudoku
        puzzle = KillerSudoku.example_4x4()
        grid = puzzle.solve()
        assert grid is not None
        for row in grid:
            assert sorted(row) == [1, 2, 3, 4]
        for c in range(4):
            col = [grid[r][c] for r in range(4)]
            assert sorted(col) == [1, 2, 3, 4]

    def test_format_solution(self):
        from lattice.puzzles.killer_sudoku import KillerSudoku
        puzzle = KillerSudoku.example_4x4()
        grid = puzzle.solve()
        formatted = puzzle.format_solution(grid)
        assert "|" in formatted
