"""
author: Adsryen <prl1594959462@gmail.com>
link: https://github.com/Adsryen/GitPorter.git
"""
import sys
from fnmatch import fnmatch
from rich.table import Table
from rich.console import Console
from gitporter.config import load_config, prepare_migrate

_SORT_MODES = [
    ("name", "按名称"),
    ("pushed", "最近推送"),
    ("updated", "最近更新"),
    ("created", "创建时间"),
]


def _sort_repos(repos: list, mode: str) -> list:
    if mode == "name":
        return sorted(repos, key=lambda r: r["name"].lower())
    key_map = {"pushed": "pushed_at", "updated": "updated_at", "created": "created_at"}
    field = key_map.get(mode, "name")
    return sorted(repos, key=lambda r: r.get(field) or "", reverse=True)


def _build_table(repos: list, sort_label: str) -> Table:
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("#", style="dim", width=5)
    table.add_column("Name")
    table.add_column("Private", width=8)
    table.add_column("Description")
    table.caption = f"排序: {sort_label}"
    for i, repo in enumerate(repos, 1):
        table.add_row(
            str(i),
            repo["name"],
            "Yes" if repo.get("is_private") else "No",
            repo.get("desc", "") or "",
        )
    return table


def run_list(cfg_file: str, filter_pattern: str = "", exclude_pattern: str = ""):
    cfg = load_config(cfg_file)
    from_git, _, repos = prepare_migrate(cfg)

    if filter_pattern:
        repos = [r for r in repos if fnmatch(r["name"], filter_pattern)]
    if exclude_pattern:
        repos = [r for r in repos if not fnmatch(r["name"], exclude_pattern)]

    if not repos:
        Console().print("[yellow]没有匹配的仓库。[/yellow]")
        return

    console = Console()
    is_tty = sys.stdin.isatty()

    if not is_tty:
        repos = _sort_repos(repos, "name")
        console.print(_build_table(repos, "按名称"))
        console.print(f"[bold]Total: {len(repos)}[/bold]")
        return

    sort_idx = 0
    while True:
        mode, label = _SORT_MODES[sort_idx]
        sorted_repos = _sort_repos(repos, mode)
        console.clear()
        console.print(_build_table(sorted_repos, label))
        console.print(f"\n[bold]Total: {len(sorted_repos)}[/bold]")
        console.print("[dim]  s 切换排序  |  Enter/q 退出[/dim]")
        try:
            ans = input().strip().lower()
        except (EOFError, KeyboardInterrupt):
            break
        if ans == "s":
            sort_idx = (sort_idx + 1) % len(_SORT_MODES)
        else:
            break
