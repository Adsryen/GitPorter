"""
author: Adsryen <prl1594959462@gmail.com>
link: https://github.com/Adsryen/GitPorter.git
"""
import sys
from gitporter.config import load_config, prepare_migrate
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn
from rich.text import Text

console = Console()


def _confirm(prompt: str) -> bool:
    try:
        ans = input(f"{prompt} [y/N]: ").strip().lower()
        return ans in ("y", "yes")
    except (EOFError, KeyboardInterrupt):
        return False


def run_sync(cfg_file: str, dry_run: bool = False, yes: bool = False, force_reclone: bool = False):
    cfg = load_config(cfg_file)
    from_git, to_git, repos = prepare_migrate(cfg)

    if not repos:
        console.print("[yellow]No repos to sync.[/yellow]")
        return

    if dry_run:
        console.print(f"\n[bold cyan]Dry run — will sync {len(repos)} repos:[/bold cyan]")
        for repo in repos:
            console.print(f"  • {repo['name']}")
        console.print("\n[dim]Use without --dry-run to execute.[/dim]")
        return

    # 非 TTY（CI 环境）跳过确认
    is_tty = sys.stdin.isatty()
    if not yes and is_tty:
        if not _confirm(f"Sync {len(repos)} repos to target?"):
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
