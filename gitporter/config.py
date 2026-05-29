"""
author: Adsryen <prl1594959462@gmail.com>
link: https://github.com/Adsryen/GitPorter.git
"""
import subprocess
import yaml
from fnmatch import fnmatch
from gitporter.git.factory import git_factory

# https://pyyaml.org/wiki/PyYAMLDocumentation
try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader


def load_config(cfg_file: str) -> dict:
    with open(cfg_file, "r") as f:
        cfg = yaml.load(f, Loader=Loader)

    return cfg


def _apply_migrate_opts(migrate_cfg: dict, provider_cfg: dict):
    """将 migrate 段的公共配置注入 provider config（provider config 优先）。"""
    for key in ("clone_dir", "clone_args", "push_args"):
        val = migrate_cfg.get(key)
        if val and key not in provider_cfg:
            provider_cfg[key] = val


def prepare_migrate(cfg: dict):
    migrate_cfg = cfg.get("migrate", None)
    if not migrate_cfg:
        raise RuntimeError("Invalid migrate")

    # 源 Git
    migrate_from = migrate_cfg.get("from", None)
    if not migrate_from:
        raise RuntimeError("Invalid migrate.from")
    migrate_from_cfg = cfg.get(migrate_from, None)
    if not migrate_from_cfg:
        raise ValueError("Not found: migrate.from cfg")
    _apply_migrate_opts(migrate_cfg, migrate_from_cfg)
    from_git = git_factory(migrate_from_cfg)

    # 目标 Git
    migrate_to = migrate_cfg.get("to", None)
    if not migrate_to:
        raise RuntimeError("Invalid migrate.to")
    migrate_to_cfg = cfg.get(migrate_to, None)
    if not migrate_to_cfg:
        raise ValueError("Not found: migrate.to cfg")
    _apply_migrate_opts(migrate_cfg, migrate_to_cfg)
    to_git = git_factory(migrate_to_cfg)

    all_repos = from_git.list_repos()
    print(f"Found {len(all_repos)} repos in {migrate_from_cfg.get('provider', '')}")

    # 白名单：只迁移指定的仓库
    cfg_repos = migrate_cfg.get("repos", [])
    if cfg_repos:
        repos = [repo for repo in all_repos if repo["name"] in cfg_repos]
    else:
        repos = list(all_repos)

    # 黑名单：排除指定的仓库，支持通配符（* 匹配任意字符，? 匹配单个字符）
    # 例如: "test_*" 排除所有 test_ 开头的仓库，"*_archive" 排除所有 _archive 结尾的仓库
    exclude_repos = migrate_cfg.get("exclude_repos", [])
    if exclude_repos:
        def is_excluded(name):
            return any(fnmatch(name, pattern) for pattern in exclude_repos)
        before = len(repos)
        repos = [repo for repo in repos if not is_excluded(repo["name"])]
        excluded = before - len(repos)
        if excluded:
            print(f"Excluded {excluded} repos by exclude_repos config")

    return from_git, to_git, repos


# ── 配置校验 ────────────────────────────────────────────

_REQUIRED_FIELDS = {
    "_common": ["provider", "token"],
    "github":  ["username", "base_api", "https_prefix"],
    "gitee":   ["username", "base_api", "https_prefix"],
    "gitlab":  ["username", "base_api", "https_prefix"],
    "gitea":   ["username", "base_api", "https_prefix"],
    "gogs":    ["username", "base_api", "https_prefix"],
    "coding":  ["username", "base_api", "https_prefix"],
    "gf":      ["username", "base_api", "https_prefix"],
    "e_gitee_v8": ["token_user", "base_api", "https_prefix", "enterprise_id"],
}


def _check_structure(name: str, cfg: dict, errors: list, warnings: list):
    """校验单个 provider 配置的结构完整性。"""
    provider = cfg.get("provider", "").lower()
    if provider == "gogs":
        provider = "gitea"

    for field in _REQUIRED_FIELDS["_common"]:
        if not cfg.get(field):
            errors.append(f"[{name}] 缺少必填字段: {field}")

    for field in _REQUIRED_FIELDS.get(provider, []):
        if not cfg.get(field):
            errors.append(f"[{name}] 缺少必填字段: {field}")

    use_https = cfg.get("use_https", False)
    ssh_prefix = cfg.get("ssh_prefix", "")

    if use_https and not cfg.get("https_prefix"):
        errors.append(f"[{name}] use_https=true 但未配置 https_prefix")

    if not use_https and not ssh_prefix:
        warnings.append(f"[{name}] 未配置 ssh_prefix 且未启用 use_https，Git 操作将不可用")


def _check_api(name: str, cfg: dict, errors: list):
    """调用 list_repos 验证 API 连通性和 token 有效性。"""
    try:
        git = git_factory(cfg)
        repos = git.list_repos()
    except Exception as e:
        errors.append(f"[{name}] API 校验失败: {e}")


def _check_git(name: str, cfg: dict, warnings: list):
    """用 git ls-remote 测试 Git 连通性。"""
    import os
    from gitporter.util import mask_auth_url

    use_https = cfg.get("use_https", False)
    ssh_prefix = cfg.get("ssh_prefix", "")
    https_prefix = cfg.get("https_prefix", "")
    token_user = cfg.get("token_user", cfg.get("username", ""))
    token = cfg.get("token", "")
    provider = cfg.get("provider", "").lower()
    username = cfg.get("username", "")

    if use_https and https_prefix:
        prefix = https_prefix.rstrip("/")
        url = f"{prefix}/{username}/_probe.git"
        if token:
            parts = prefix.split("://")
            url = f"{parts[0]}://{token_user}:{token}@{parts[1]}/{username}/_probe.git"
    elif ssh_prefix:
        url = f"{ssh_prefix}:{username}/_probe.git"
    else:
        warnings.append(f"[{name}] 跳过 Git 连通检查（无可用地址）")
        return

    try:
        ret = subprocess.run(
            ["git", "ls-remote", url],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding="utf-8",
            timeout=15,
        )
        # ls-remote 对不存在的仓库返回 128，但只要能连上（有 stderr 输出）就说明认证通过
        # 如果是认证失败（401/403），stderr 会有明确错误信息
        stderr = ret.stderr.strip()
        if ret.returncode != 0:
            if "Authentication" in stderr or "401" in stderr or "403" in stderr or "Permission" in stderr:
                errors.append(f"[{name}] Git 认证失败: {mask_auth_url(stderr)}")
            # 其他非 0（如 128，仓库不存在）说明认证通过，只是仓库不存在，这是正常的
    except subprocess.TimeoutExpired:
        warnings.append(f"[{name}] Git 连通检查超时（15s）")
    except Exception as e:
        warnings.append(f"[{name}] Git 连通检查异常: {e}")


def validate_config(cfg_file: str):
    """校验配置文件：结构 → API 连通 → Git 连通。返回 (errors, warnings)。"""
    try:
        cfg = load_config(cfg_file)
    except FileNotFoundError:
        return [f"配置文件不存在: {cfg_file}"], []
    except yaml.YAMLError as e:
        return [f"YAML 解析失败: {e}"], []
    except Exception as e:
        return [f"加载配置失败: {e}"], []

    errors = []
    warnings = []

    migrate_cfg = cfg.get("migrate")
    if not migrate_cfg:
        errors.append("缺少 migrate 段")
        return errors, warnings

    from_key = migrate_cfg.get("from")
    to_key = migrate_cfg.get("to")
    if not from_key:
        errors.append("缺少 migrate.from")
    if not to_key:
        errors.append("migrate.to")
    if from_key == to_key:
        errors.append("migrate.from 和 migrate.to 不能相同")

    # 结构校验
    for key in (from_key, to_key):
        if not key:
            continue
        provider_cfg = cfg.get(key)
        if not provider_cfg:
            errors.append(f"缺少 [{key}] 配置段")
            continue
        _check_structure(key, provider_cfg, errors, warnings)

    if errors:
        return errors, warnings

    # API 连通校验
    for key in (from_key, to_key):
        if not key:
            continue
        provider_cfg = cfg.get(key)
        if not provider_cfg:
            continue
        _apply_migrate_opts(migrate_cfg, provider_cfg)
        _check_api(key, provider_cfg, errors)

    if errors:
        return errors, warnings

    # Git 连通校验
    for key in (from_key, to_key):
        if not key:
            continue
        provider_cfg = cfg.get(key)
        if not provider_cfg:
            continue
        _check_git(key, provider_cfg, warnings)

    return errors, warnings
