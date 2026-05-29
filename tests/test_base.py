"""gitporter.git.base._extract_git_error 单元测试"""
from gitporter.git.base import _extract_git_error


class TestExtractGitError:
    def test_filters_progress_lines(self):
        stderr = (
            "Enumerating objects: 37660, done.\n"
            "Counting objects: 100% (37660/37660), done.\n"
            "Delta compression using up to 4 threads\n"
            "Compressing objects: 100% (15185/15185), done.\n"
            "Writing objects: 100% (37660/37660), done.\n"
            "Total 37660 (delta 15978), reused 37660 (delta 15978)\n"
            "error: RPC failed; HTTP 413\n"
            "fatal: the remote end hung up unexpectedly\n"
            "Everything up-to-date"
        )
        result = _extract_git_error(stderr)
        assert "Counting objects" not in result
        assert "Writing objects" not in result
        assert "Delta compression" not in result
        assert "Everything up-to-date" not in result
        assert "error: RPC failed; HTTP 413" in result
        assert "fatal: the remote end hung up unexpectedly" in result

    def test_auth_error_preserved(self):
        stderr = (
            "remote: Unauthorized\n"
            "fatal: Authentication failed for 'https://github.com/repo.git'"
        )
        result = _extract_git_error(stderr)
        assert "Authentication failed" in result

    def test_only_progress_returns_original(self):
        stderr = "Counting objects: 100% (100/100), done."
        result = _extract_git_error(stderr)
        # 只有进度行时返回原始内容
        assert result == stderr

    def test_empty_stderr(self):
        result = _extract_git_error("")
        assert result == ""

    def test_percentage_line_filtered(self):
        stderr = "  42% (1000/2380)\nerror: something failed"
        result = _extract_git_error(stderr)
        assert "42%" not in result
        assert "error: something failed" in result
