"""gitporter.sync._parse_selection 单元测试"""
from gitporter.sync import _parse_selection


class TestParseSelection:
    def test_single_number(self):
        assert _parse_selection("3", 10) == {2}

    def test_multiple_numbers(self):
        assert _parse_selection("1,3,5", 10) == {0, 2, 4}

    def test_range(self):
        assert _parse_selection("3-6", 10) == {2, 3, 4, 5}

    def test_range_reversed(self):
        assert _parse_selection("6-3", 10) == {2, 3, 4, 5}

    def test_mixed(self):
        assert _parse_selection("1,3-5,8", 10) == {0, 2, 3, 4, 7}

    def test_out_of_range_ignored(self):
        result = _parse_selection("1,99", 10)
        assert result == {0}

    def test_empty_string(self):
        assert _parse_selection("", 10) == set()

    def test_invalid_input(self):
        assert _parse_selection("abc", 10) == set()

    def test_partial_invalid(self):
        result = _parse_selection("1,abc,3", 10)
        assert result == {0, 2}

    def test_boundary(self):
        assert _parse_selection("1,10", 10) == {0, 9}

    def test_spaces(self):
        assert _parse_selection(" 1 , 3 - 5 ", 10) == {0, 2, 3, 4}
