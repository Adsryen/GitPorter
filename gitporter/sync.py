"""
author: Adsryen <prl1594959462@gmail.com>
link: https://github.com/Adsryen/GitPorter.git
"""
import sys
from gitporter.config import load_config, prepare_migrate
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn
from rich.text import Text

console = Console()


def _confirm(prompt: str) -> bool:
    try:
        ans = input(f"{prompt} [y/N]: ").strip().lower()
        return ans in ("y", "yes")
    except (EOFError, KeyboardInterrupt):
        return False


def _parse_selection(text: str, max_index: int) -> set:
    """解析用户输入的选择项，支持：单个(1)、多个(1,3,5)、范围(3-8)、混合(1,3-5,8)。
    返回 0-based 索引集合。"""
    indices = set()
    for part in text.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            try:
                start, end = part.split("-", 1)
                start, end = int(start.strip()), int(end.strip())
                if start > end:
                    start, end = end, start
                for i in range(start, end + 1):
                    if 1 <= i <= max_index:
                        indices.add(i - 1)
            except ValueError:
                continue
        else:
            try:
                i = int(part)
                if 1 <= i <= max_index:
                    indices.add(i - 1)
            except ValueError:
                continue
    return indices


def _select_repos(repos: list) -> list:
    """显示带编号的仓库列表，让用户交互式选择。返回选中的仓库子集。"""
    table = Table(show_lines=False, show_edge=False, pad_edge=False)
    table.add_column("#", justify="right", style="dim", no_wrap=True)
    table.add_column("仓库名", no_wrap=True)
    table.add_column("说明", style="dim")
    for i, repo in enumerate(repos, 1):
        desc = repo.get("desc") or ""
        table.add_row(str(i), repo["name"], desc[:50])

    console.print(table)
    console.print()
    console.print("[dim]支持格式: 1,3,5  |  3-8  |  1,3-5,8  |  all  |  q 退出[/dim]")

    while True:
        try:
            choice = input("\n选择要同步的仓库: ").strip()
        except (EOFError, KeyboardInterrupt):
            return []

        if not choice or choice.lower() == "q":
            return []
        if choice.lower() == "all":
            return repos

        indices = _parse_selection(choice, len(repos))
        if not indices:
            console.print("[yellow]输入无效，请重新输入。[/yellow]")
            continue

        selected = [repos[i] for i in sorted(indices)]
        console.print(f"\n已选择 {len(selected)} 个仓库:")
        for repo in selected:
            console.print(f"  • {repo['name']}")

        if _confirm("确认同步以上仓库？"):
            return selected
        else:
            console.print("[yellow]已取消，请重新选择。[/yellow]")


def run_sync(cfg_file: str, dry_run: bool = False, yes: bool = False, force_reclone: bool = False, select: bool = False):
    cfg = load_config(cfg_file)
    from_git, to_git, repos = prepare_migrate(cfg)

    if not repos:
        console.print("[yellow]No repos to sync.[/yellow]")
        return

    # 交互式选择仓库
    if select:
        repos = _select_repos(repos)
        if not repos:
            console.print("[yellow]未选择任何仓库，退出。[/yellow]")
            return

    if dry_run:
        console.print(f"\n[bold cyan]Dry run — will sync {len(repos)} repos:[/bold cyan]")
        for repo in repos:
            console.print(f"  • {repo['name']}")
        console.print("\n[dim]Use without --dry-run to execute.[/dim]")
        return

    # 非 TTY（CI 环境）跳过确认
    is_tty = sys.stdin.isatty()
    if not yes and not select and is_tty:
        console.print(f"\n[bold]待同步仓库（{len(repos)} 个）:[/bold]")
        for repo in repos:
            console.print(f"  • {repo['name']}")
        if not _confirm(f"\n确认同步以上仓库到目标平台？"):
            console.print("[yellow]Aborted.[/yellow]")
            return

    success_count = 0
    fail_count = 0

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TextColumn("{task.completed}/{task.total}"),
        TimeElapsedColumn(),
        console=console,
        transient=False,
    ) as progress:
        task = progress.add_task("Syncing...", total=len(repos))

        for repo in repos:
            repo_name = repo["name"]
            progress.update(task, description=f"[cyan]{repo_name}[/cyan]")

            try:
                repo_dir, clone_err, action = from_git.clone_repo(
                    repo_name,
                    repo_owner=repo.get("owner", ""),
                    force_reclone=force_reclone,
                )
                if not repo_dir:
                    console.print(f"[red][FAIL][/red] {action} [bold]{repo_name}[/bold]: {clone_err}")
                    fail_count += 1
                    progress.advance(task)
                    continue

                has_create = to_git.create_repo(
                    name=repo_name,
                    desc=repo.get("desc", ""),
                    is_private=repo.get("is_private", True),
                )
                if not has_create:
                    if to_git.is_repo_existed(repo_name):
                        console.print(f"[yellow][WARN][/yellow] [bold]{repo_name}[/bold]: already exists on target, pushing anyway")
                    else:
                        console.print(f"[red][FAIL][/red] create [bold]{repo_name}[/bold]: API returned non-success status")
                        fail_count += 1
                        progress.advance(task)
                        continue

                ok, push_err = to_git.push_repo(repo_name, repo_dir)
                if ok:
                    console.print(f"[green][OK][/green]   {action}+push [bold]{repo_name}[/bold]")
                    success_count += 1
                else:
                    console.print(f"[red][FAIL][/red] push [bold]{repo_name}[/bold]: {push_err}")
                    fail_count += 1

            except Exception as e:
                console.print(f"[red][FAIL][/red] [bold]{repo_name}[/bold]: {e}")
                fail_count += 1

            progress.advance(task)

    color = "green" if fail_count == 0 else "yellow"
    console.print(
        f"\n[{color}]Migration finished:[/{color}] "
        f"[green]{success_count} succeeded[/green], "
        f"[red]{fail_count} failed[/red], "
        f"{len(repos)} total"
    )
