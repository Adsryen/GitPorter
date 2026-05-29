"""gitporter.util 单元测试"""
from gitporter.util import mask_secret, mask_auth_url


class TestMaskSecret:
    def test_masks_long_token(self):
        text = "Error: token ghp_abc123xyz failed"
        result = mask_secret(text, "ghp_abc123xyz")
        assert "ghp_abc123xyz" not in result
        assert "ghp****xyz" in result

    def test_masks_short_token(self):
        result = mask_secret("abc", "abc")
        assert result == "****"

    def test_empty_secret(self):
        result = mask_secret("hello", "")
        assert result == "hello"

    def test_multiple_occurrences(self):
        text = "ghp_abc123xyz and ghp_abc123xyz again"
        result = mask_secret(text, "ghp_abc123xyz")
        assert result.count("ghp****xyz") == 2

    def test_no_match(self):
        result = mask_secret("hello world", "token")
        assert result == "hello world"


class TestMaskAuthUrl:
    def test_masks_user_token_url(self):
        url = "https://user:ghp_secret@github.com/repo.git"
        result = mask_auth_url(url)
        assert "ghp_secret" not in result
        assert "user:****@github.com" in result

    def test_no_auth_part(self):
        url = "https://github.com/repo.git"
        result = mask_auth_url(url)
        assert result == url

    def test_preserves_schema(self):
        url = "http://user:token123@gitea.example.com/api/v1"
        result = mask_auth_url(url)
        assert result.startswith("http://")
        assert "user:****@gitea" in result
