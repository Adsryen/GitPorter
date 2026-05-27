"""
author: Adsryen <prl1594959462@gmail.com>
link: https://github.com/Adsryen/GitPorter.git
"""
from fnmatch import fnmatch
from rich.table import Table
from rich.console import Console
from gitporter.config import load_config, prepare_migrate


def run_list(cfg_file: str, filter_pattern: str = "", exclude_pattern: str = ""):
    cfg = load_config(cfg_file)
    from_git, _, repos = prepare_migrate(cfg)

    if filter_pattern:
        repos = [r for r in repos if fnmatch(r["name"], filter_pattern)]
    if exclude_pattern:
        repos = [r for r in repos if not fnmatch(r["name"], exclude_pattern)]

    console = Console()
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("#", style="dim", width=5)
    table.add_column("Name")
    table.add_column("Private", width=8)
    table.add_column("Description")

    for i, repo in enumerate(repos, 1):
        table.add_row(
            str(i),
            repo["name"],
            "Yes" if repo.get("is_private") else "No",
            repo.get("desc", "") or "",
        )

    console.print(table)
    console.print(f"[bold]Total: {len(repos)}[/bold]")
