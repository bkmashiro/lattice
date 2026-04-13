"""Tests for the CLI interface."""

import pytest
from lattice.cli import main


class TestCLI:
    def test_no_args(self):
        result = main([])
        assert result == 0

    def test_sudoku_easy(self):
        result = main(["sudoku", "--example", "easy"])
        assert result == 0

    def test_sudoku_4x4(self):
        result = main(["sudoku", "--example", "4x4"])
        assert result == 0

    def test_sudoku_string(self):
        puzzle = (
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
        result = main(["sudoku", puzzle])
        assert result == 0

    def test_sudoku_no_input(self):
        result = main(["sudoku"])
        assert result == 1

    def test_nqueens_4(self):
        result = main(["nqueens", "4"])
        assert result == 0

    def test_nqueens_8(self):
        result = main(["nqueens", "8"])
        assert result == 0

    def test_nqueens_count(self):
        result = main(["nqueens", "4", "--count"])
        assert result == 0

    def test_coloring_australia(self):
        result = main(["coloring", "australia"])
        assert result == 0

    def test_coloring_petersen(self):
        result = main(["coloring", "petersen"])
        assert result == 0

    def test_coloring_cycle(self):
        result = main(["coloring", "cycle", "3", "--nodes", "5"])
        assert result == 0

    def test_kenken_4x4(self):
        result = main(["kenken", "--example", "4x4"])
        assert result == 0

    def test_nonogram_heart(self):
        result = main(["nonogram", "--example", "heart"])
        assert result == 0

    def test_nonogram_cross(self):
        result = main(["nonogram", "--example", "cross"])
        assert result == 0

    def test_crypto_send(self):
        result = main(["crypto", "--example", "send"])
        assert result == 0

    def test_futoshiki(self):
        result = main(["futoshiki"])
        assert result == 0

    def test_killer(self):
        result = main(["killer"])
        assert result == 0

    def test_magic_3(self):
        result = main(["magic", "3"])
        assert result == 0

    def test_propagation_fc(self):
        result = main(["-p", "fc", "nqueens", "4"])
        assert result == 0

    def test_propagation_none(self):
        result = main(["-p", "none", "nqueens", "4"])
        assert result == 0

    def test_explain_flag(self):
        result = main(["-e", "sudoku", "--example", "4x4"])
        assert result == 0
