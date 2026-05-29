"""
author: Adsryen <prl1594959462@gmail.com>
link: https://github.com/Adsryen/GitPorter.git
"""
import os
import yaml

try:
    from yaml import CDumper as Dumper
except ImportError:
    from yaml import Dumper


_TOKEN_KEYS = {"token", "web_cookie"}

PROVIDER_DEFAULTS = {
    "github": {
        "provider": "github",
        "base_api": "https://api.github.com/graphql",
        "ssh_prefix": "git@github.com",
        "https_prefix": "https://github.com",
        "username": "",
        "token": "",
        "use_https": True,
    },
    "gitee": {
        "provider": "gitee",
        "base_api": "https://gitee.com/api/v5",
        "ssh_prefix": "git@gitee.com",
        "https_prefix": "https://gitee.com",
        "username": "",
        "token": "",
    },
    "gitlab": {
        "provider": "gitlab",
        "base_api": "https://gitlab.com/api/v4",
        "ssh_prefix": "git@gitlab.com",
        "https_prefix": "https://gitlab.com",
        "username": "",
        "token": "",
    },
    "gitea": {
        "provider": "gitea",
        "base_api": "https://gitea.com/api/v1",
        "ssh_prefix": "git@gitea.com",
        "https_prefix": "https://gitea.com",
        "username": "",
        "token": "",
    },
    "gogs": {
        "provider": "gogs",
        "base_api": "https://try.gogs.io/api/v1",
        "ssh_prefix": "git@gogs.io",
        "https_prefix": "https://gogs.io",
        "username": "",
        "token": "",
    },
    "coding": {
        "provider": "coding",
        "base_api": "https://{your-team}.coding.net",
        "ssh_prefix": "git@e.coding.net",
        "https_prefix": "https://e.coding.net",
        "username": "",
        "token": "",
        "org_name": "",
        "is_org": False,
        "use_web_base_api": True,
        "use_https": True,
        "web_cookie": "",
    },
    "gf": {
        "provider": "gf",
        "base_api": "https://code.tencent.com/api/v3",
        "ssh_prefix": "git@git.code.tencent.com",
        "https_prefix": "https://git.code.tencent.com",
        "username": "",
        "token": "",
    },
    "e_gitee_v8": {
        "provider": "e_gitee_v8",
        "base_api": "https://api.gitee.com/enterprises",
        "https_prefix": "https://gitee.com",
        "enterprise_id": "",
        "token": "",
        "token_user": "",
        "use_https": True,
    },
}


def _prompt(msg, default=""):
    val = input(f"{msg} [{default}]: ").strip() if default else input(f"{msg}: ").strip()
    return val if val else default


def _mask(cfg: dict) -> dict:
    masked = {}
    for k, v in cfg.items():
        if isinstance(v, dict):
            masked[k] = _mask(v)
        elif k in _TOKEN_KEYS and v:
            masked[k] = v[:4] + "****"
        else:
            masked[k] = v
    return masked


def run_config(output: str, show: bool = False, cfg_file: str = ""):
    if show:
        path = cfg_file or output
        if not os.path.exists(path):
            print(f"Config file not found: {path}")
            return
        with open(path) as f:
            try:
                from yaml import CLoader as Loader
            except ImportError:
                from yaml import Loader
            cfg = yaml.load(f, Loader=Loader)
        print(yaml.dump(_mask(cfg), allow_unicode=True, default_flow_style=False))
        return

    print("=== GitPorter 交互式配置向导 ===\n")
    providers = list(PROVIDER_DEFAULTS.keys())
    print("支持的平台:", ", ".join(providers))

    from_key = _prompt("迁移源平台 (from)")
    to_key = _prompt("迁移目标平台 (to)")

    cfg = {
        "migrate": {
            "from": from_key,
            "to": to_key,
            "clone_dir": _prompt("本地克隆目录 (clone_dir)", ""),
        }
    }

    for key in (from_key, to_key):
        defaults = PROVIDER_DEFAULTS.get(key, {"provider": key})
        print(f"\n--- 配置 [{key}] ---")
        section = {}
        for field, default in defaults.items():
            if field == "provider":
                section[field] = key
                continue
            val = _prompt(f"  {field}", str(default) if default != "" else "")
            if isinstance(default, bool):
                section[field] = val.lower() in ("true", "1", "yes")
            else:
                section[field] = val
        cfg[key] = section

    with open(output, "w") as f:
        yaml.dump(cfg, f, allow_unicode=True, default_flow_style=False)
    print(f"\n配置已写入: {output}")


def run_validate(cfg_file: str):
    from gitporter.config import validate_config
    from rich.console import Console
    from rich.panel import Panel

    console = Console()
    console.print(f"\n[bold]校验配置文件: {cfg_file}[/bold]\n")

    errors, warnings = validate_config(cfg_file)

    if warnings:
        console.print(Panel("\n".join(f"[yellow]⚠[/yellow]  {w}" for w in warnings),
                            title="[yellow]Warnings[/yellow]", border_style="yellow"))

    if errors:
        console.print(Panel("\n".join(f"[red]✗[/red]  {e}" for e in errors),
                            title="[red]Errors[/red]", border_style="red"))
        console.print("\n[red]配置校验未通过，请修复以上错误后再运行 sync。[/red]")
    else:
        console.print(Panel("[green]✓ 结构校验通过\n✓ API 连通性正常\n✓ Git 连通性正常[/green]",
                            title="[green]All Checks Passed[/green]", border_style="green"))
        console.print("\n[green]配置校验通过，可以运行 [bold]gitporter sync[/bold] 开始迁移。[/green]")
