"""
author: Adsryen <prl1594959462@gmail.com>
link: https://github.com/Adsryen/GitPorter.git
"""
import sys
from fnmatch import fnmatch
from rich.table import Table
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
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


def _build_table(repos: list, sort_label: str, status_map: dict = None) -> Table:
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("#", style="dim", width=5)
    table.add_column("Name")
    table.add_column("Private", width=8)
    if status_map is not None:
        table.add_column("Synced", width=6, justify="center")
    table.add_column("Description")
    table.caption = f"排序: {sort_label}"
    for i, repo in enumerate(repos, 1):
        row = [str(i), repo["name"], "Yes" if repo.get("is_private") else "No"]
        if status_map is not None:
            synced = status_map.get(repo["name"], False)
            row.append("[green]✓[/green]" if synced else "[dim]-[/dim]")
        row.append(repo.get("desc", "") or "")
        table.add_row(*row)
    return table


def _check_sync_status(to_git, repos: list, console: Console) -> dict:
    """检查每个仓库是否已存在于目标平台，返回 {name: bool}。"""
    status_map = {}
    with Progress(SpinnerColumn(), TextColumn("{task.description}"), console=console) as progress:
        task = progress.add_task("检查同步状态...", total=len(repos))
        for repo in repos:
            try:
                status_map[repo["name"]] = to_git.is_repo_existed(repo["name"])
            except Exception:
                status_map[repo["name"]] = False
            progress.advance(task)
    return status_map


def run_list(cfg_file: str, filter_pattern: str = "", exclude_pattern: str = "",
             status: bool = False, limit: int = 0, search_keyword: str = ""):
    cfg = load_config(cfg_file)
    from_git, to_git, repos = prepare_migrate(cfg)

    if filter_pattern:
        repos = [r for r in repos if fnmatch(r["name"], filter_pattern)]
    if search_keyword:
        kw = search_keyword.lower()
        repos = [r for r in repos if kw in r["name"].lower() or kw in (r.get("desc") or "").lower()]
    if exclude_pattern:
        repos = [r for r in repos if not fnmatch(r["name"], exclude_pattern)]

    if limit > 0:
        repos = repos[:limit]

    if not repos:
        Console().print("[yellow]没有匹配的仓库。[/yellow]")
        return

    console = Console()
    status_map = None
    if status:
        status_map = _check_sync_status(to_git, repos, console)

    is_tty = sys.stdin.isatty()

    if not is_tty:
        repos = _sort_repos(repos, "name")
        console.print(_build_table(repos, "按名称", status_map))
        console.print(f"[bold]Total: {len(repos)}[/bold]")
        if status_map:
            synced = sum(1 for v in status_map.values() if v)
            console.print(f"[green]已同步: {synced}[/green] / [dim]未同步: {len(repos) - synced}[/dim]")
        return

    sort_idx = 0
    while True:
        mode, label = _SORT_MODES[sort_idx]
        sorted_repos = _sort_repos(repos, mode)
        console.clear()
        console.print(_build_table(sorted_repos, label, status_map))
        console.print(f"\n[bold]Total: {len(sorted_repos)}[/bold]")
        if status_map:
            synced = sum(1 for r in sorted_repos if status_map.get(r["name"], False))
            console.print(f"[green]已同步: {synced}[/green] / [dim]未同步: {len(sorted_repos) - synced}[/dim]")
        console.print("[dim]  s 切换排序  |  Enter/q 退出[/dim]")
        try:
            ans = input().strip().lower()
        except (EOFError, KeyboardInterrupt):
            break
        if ans == "s":
            sort_idx = (sort_idx + 1) % len(_SORT_MODES)
        else:
            break
