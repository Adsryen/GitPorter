"""
author: Adsryen <prl1594959462@gmail.com>
link: https://github.com/Adsryen/GitPorter.git
"""
from gitporter.git.base import Git
from gitporter.git import gitlab, github, gitee, gitea, coding, gongfeng, e_gitee_v8


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
