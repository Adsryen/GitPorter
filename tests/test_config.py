"""gitporter.config 单元测试"""
import os
import tempfile
import yaml
from gitporter.config import load_config, validate_config, _check_structure


class TestLoadConfig:
    def test_load_valid_yaml(self, tmp_path):
        cfg_file = tmp_path / "test.yml"
        cfg_file.write_text("migrate:\n  from: github\n  to: gitee\n")
        cfg = load_config(str(cfg_file))
        assert cfg["migrate"]["from"] == "github"

    def test_file_not_found(self):
        errors, warnings = validate_config("/nonexistent/path.yml")
        assert any("不存在" in e for e in errors)


class TestCheckStructure:
    def test_missing_token(self):
        cfg = {"provider": "github", "username": "user"}
        errors, warnings = [], []
        _check_structure("test", cfg, errors, warnings)
        assert any("token" in e for e in errors)

    def test_use_https_without_https_prefix(self):
        cfg = {"provider": "github", "token": "t", "username": "u",
               "base_api": "https://api.github.com", "use_https": True}
        errors, warnings = [], []
        _check_structure("test", cfg, errors, warnings)
        assert any("https_prefix" in e for e in errors)

    def test_no_ssh_no_https_warns(self):
        cfg = {"provider": "gitea", "token": "t", "username": "u",
               "base_api": "https://gitea.com/api/v1", "https_prefix": "https://gitea.com"}
        errors, warnings = [], []
        _check_structure("test", cfg, errors, warnings)
        assert not errors
        assert any("ssh_prefix" in w for w in warnings)

    def test_valid_config(self):
        cfg = {"provider": "github", "token": "ghp_xxx", "username": "user",
               "base_api": "https://api.github.com/graphql",
               "ssh_prefix": "git@github.com", "https_prefix": "https://github.com",
               "use_https": True}
        errors, warnings = [], []
        _check_structure("test", cfg, errors, warnings)
        assert not errors


class TestValidateConfig:
    def _write_cfg(self, tmp_path, cfg):
        cfg_file = tmp_path / "test.yml"
        cfg_file.write_text(yaml.dump(cfg, allow_unicode=True))
        return str(cfg_file)

    def test_missing_migrate(self, tmp_path):
        path = self._write_cfg(tmp_path, {"github": {"provider": "github"}})
        errors, _ = validate_config(path)
        assert any("migrate" in e.lower() for e in errors)

    def test_same_from_to(self, tmp_path):
        path = self._write_cfg(tmp_path, {
            "migrate": {"from": "github", "to": "github"},
            "github": {"provider": "github", "token": "t"}
        })
        errors, _ = validate_config(path)
        assert any("不能相同" in e for e in errors)

    def test_missing_provider_section(self, tmp_path):
        path = self._write_cfg(tmp_path, {
            "migrate": {"from": "github", "to": "gitee"},
            "github": {"provider": "github", "token": "t", "username": "u",
                        "base_api": "https://api.github.com/graphql",
                        "https_prefix": "https://github.com"}
        })
        errors, _ = validate_config(path)
        assert any("gitee" in e for e in errors)

    def test_invalid_yaml(self, tmp_path):
        cfg_file = tmp_path / "bad.yml"
        cfg_file.write_text("{{invalid yaml")
        errors, _ = validate_config(str(cfg_file))
        assert any("YAML" in e or "加载" in e for e in errors)
