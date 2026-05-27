"""
author: K8sCat <k8scat@gmail.com>
link: https://github.com/k8scat/gigrator.git
"""
import yaml
from fnmatch import fnmatch
from gigrator.git.git import Git
from gigrator.git import gitlab, github, gitee, gitea, coding, gongfeng, e_gitee_v8

# https://pyyaml.org/wiki/PyYAMLDocumentation
try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader


def load_config(cfg_file: str) -> dict:
    with open(cfg_file, "r") as f:
        cfg = yaml.load(f, Loader=Loader)

    return cfg


def git_factory(cfg: dict) -> Git:
    provider = cfg.get("provider", "")
    if not provider:
        raise RuntimeError("Invalid provider")

    if provider == "gitlab":
        return gitlab.Gitlab(cfg)
    if provider == "github":
        return github.Github(cfg)
    if provider == "coding":
        return coding.Coding(cfg)
    if provider in ["gitea", "gogs"]:
        return gitea.Gitea(cfg)
    if provider == "gitee":
        return gitee.Gitee(cfg)
    if provider == "gf":
        return gongfeng.GF(cfg)
    if provider == "e_gitee_v8":
        return e_gitee_v8.Gitee(cfg)

    raise ValueError(f"Invalid provider: {provider}")


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
