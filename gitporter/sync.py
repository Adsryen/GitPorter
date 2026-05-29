"""
author: Adsryen <prl1594959462@gmail.com>
link: https://github.com/Adsryen/GitPorter.git
"""
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from gitporter.config import load_config, prepare_migrate
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn
from rich.text import Text

console = Console()

_FAILED_FILE = ".last_failed.json"


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
    """显示带编号的仓库列表，支持排序切换、搜索过滤和交互式选择。"""
    from gitporter.commands.list_cmd import _sort_repos, _SORT_MODES, _build_table

    sort_idx = 0
    search = ""

    while True:
        mode, label = _SORT_MODES[sort_idx]
        sorted_repos = _sort_repos(repos, mode)
        if search:
            filtered = [r for r in sorted_repos if search.lower() in r["name"].lower()]
        else:
            filtered = sorted_repos

        console.clear()
        if search:
            console.print(f"[bold]搜索: [cyan]{search}[/cyan][/bold]  "
                          f"匹配 {len(filtered)}/{len(repos)}  "
                          f"[dim](按 c 清除搜索)[/dim]\n")
        console.print(_build_table(filtered, label))
        console.print()
        console.print("[dim]  s 切换排序  |  / 搜索  |  输入序号选择  |  all 全选  |  q 退出[/dim]")
        console.print("[dim]  支持: 1,3,5  |  3-8  |  1,3-5,8[/dim]")

        try:
            choice = input("\n> ").strip()
        except (EOFError, KeyboardInterrupt):
            return []

        if not choice or choice.lower() == "q":
            return []
        if choice.lower() == "s":
            sort_idx = (sort_idx + 1) % len(_SORT_MODES)
            continue
        if choice == "/":
            try:
                search = input("搜索仓库名: ").strip()
            except (EOFError, KeyboardInterrupt):
                search = ""
            continue
        if choice.lower() == "c":
            search = ""
            continue
        if choice.lower() == "all":
            return filtered

        indices = _parse_selection(choice, len(filtered))
        if not indices:
            console.print("[yellow]输入无效，请重新输入。[/yellow]")
            continue

        selected = [filtered[i] for i in sorted(indices)]
        console.print(f"\n已选择 {len(selected)} 个仓库:")
        for repo in selected:
            console.print(f"  • {repo['name']}")

        if _confirm("确认同步以上仓库？"):
            return selected
        else:
            console.print("[yellow]已取消，请重新选择。[/yellow]")


def _save_failed(clone_dir: str, failed: list):
    """将失败仓库列表写入 .gitporter/.last_failed.json。"""
    if not clone_dir:
        return
    path = os.path.join(clone_dir, _FAILED_FILE)
    try:
        with open(path, "w") as f:
            json.dump({"failed": failed, "time": time.strftime("%Y-%m-%d %H:%M:%S")}, f, ensure_ascii=False, indent=2)
    except OSError:
        pass


def _load_failed(clone_dir: str) -> list:
    """读取上次失败的仓库列表。"""
    path = os.path.join(clone_dir, _FAILED_FILE)
    if not os.path.exists(path):
        return []
    try:
        with open(path) as f:
            data = json.load(f)
        return data.get("failed", [])
    except (OSError, json.JSONDecodeError):
        return []


def _sync_one(repo: dict, from_git, to_git, force_reclone: bool, lock: Lock,
              progress, task_id) -> tuple:
    """同步单个仓库，返回 (repo, success: bool, message: str, action: str)。"""
    repo_name = repo["name"]
    try:
        repo_dir, clone_err, action = from_git.clone_repo(
            repo_name, repo_owner=repo.get("owner", ""), force_reclone=force_reclone,
        )
        if not repo_dir:
            return repo, False, f"{action} {repo_name}: {clone_err}", action

        has_create = to_git.create_repo(
            name=repo_name, desc=repo.get("desc", ""), is_private=repo.get("is_private", True),
        )
        if not has_create:
            if to_git.is_repo_existed(repo_name):
                pass  # already exists, will push anyway
            else:
                return repo, False, f"create {repo_name}: API returned non-success status", action

        ok, push_err = to_git.push_repo(repo_name, repo_dir)
        if ok:
            return repo, True, f"{action}+push {repo_name}", action
        return repo, False, f"push {repo_name}: {push_err}", action

    except Exception as e:
        return repo, False, f"{repo_name}: {e}", ""


def run_sync(cfg_file: str, dry_run: bool = False, yes: bool = False,
             force_reclone: bool = False, select: bool = False,
             retry: bool = False, repos_pattern: str = "", workers: int = 1):
    cfg = load_config(cfg_file)
    from_git, to_git, repos = prepare_migrate(cfg)

    if not repos:
        console.print("[yellow]No repos to sync.[/yellow]")
        return

    # --repos: 命令行直接指定仓库名
    if repos_pattern:
        names = {n.strip() for n in repos_pattern.split(",") if n.strip()}
        repos = [r for r in repos if r["name"] in names]
        not_found = names - {r["name"] for r in repos}
        if not_found:
            console.print(f"[yellow]未找到的仓库: {', '.join(sorted(not_found))}[/yellow]")
        if not repos:
            console.print("[yellow]没有匹配的仓库。[/yellow]")
            return

    # --retry: 读取上次失败的仓库，只重试这些
    if retry:
        failed_names = _load_failed(from_git.clone_dir)
        if not failed_names:
            console.print("[green]没有需要重试的仓库。[/green]")
            return
        repos = [r for r in repos if r["name"] in failed_names]
        console.print(f"[cyan]重试上次失败的 {len(repos)} 个仓库[/cyan]")

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
    failed_repos = []
    workers = max(1, workers)
    start_time = time.time()

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
        lock = Lock()

        def _on_done(future):
            repo, ok, msg, action = future.result()
            with lock:
                if ok:
                    console.print(f"[green][OK][/green]   {msg}")
                    nonlocal success_count
                    success_count += 1
                else:
                    console.print(f"[red][FAIL][/red] {msg}")
                    nonlocal fail_count
                    fail_count += 1
                    failed_repos.append(repo)
                progress.advance(task)

        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = []
            for repo in repos:
                f = pool.submit(_sync_one, repo, from_git, to_git, force_reclone,
                                lock, progress, task)
                f.add_done_callback(_on_done)
                futures.append(f)
            # 等待所有任务完成
            for f in futures:
                f.result()

    color = "green" if fail_count == 0 else "yellow"
    elapsed = time.time() - start_time
    if elapsed >= 60:
        elapsed_str = f"{int(elapsed // 60)}m{int(elapsed % 60)}s"
    else:
        elapsed_str = f"{elapsed:.1f}s"
    console.print(
        f"\n[{color}]Migration finished:[/{color}] "
        f"[green]{success_count} succeeded[/green], "
        f"[red]{fail_count} failed[/red], "
        f"{len(repos)} total, "
        f"[cyan]{elapsed_str}[/cyan]"
    )

    # 保存失败记录供 --retry 使用
    if failed_repos:
        _save_failed(from_git.clone_dir, [r["name"] for r in failed_repos])
        console.print(f"[dim]已保存失败记录，可通过 gitporter sync --retry 重试[/dim]")
    elif os.path.exists(os.path.join(from_git.clone_dir, _FAILED_FILE)):
        os.remove(os.path.join(from_git.clone_dir, _FAILED_FILE))
