"""
author: Adsryen <prl1594959462@gmail.com>
link: https://github.com/Adsryen/GitPorter.git
"""
import argparse
import locale
from gitporter.util import git_version


def _is_chinese() -> bool:
    """检测系统语言是否为中文。"""
    try:
        lang = locale.getlocale()[0] or locale.getdefaultlocale()[0] or ""
        return lang.startswith("zh")
    except Exception:
        return False


def precheck():
    git_version()


def _build_parser() -> argparse.ArgumentParser:
    zh = _is_chinese()

    if zh:
        desc = "GitPorter — Git 代码仓批量迁移 & 持续同步工具"
        epilog = (
            "快速开始:\n"
            "  1. cp config.yml.example config.yml   复制配置模板\n"
            "  2. gitporter config --validate         校验配置是否正确\n"
            "  3. gitporter sync --dry-run            预演，确认无误后执行\n"
            "  4. gitporter sync                      开始同步\n"
            "\n"
            "常用场景:\n"
            "  gitporter list --search keyword        按关键词搜索仓库\n"
            "  gitporter list --status                查看哪些仓库已同步\n"
            "  gitporter sync --select                交互式挑选仓库同步\n"
            "  gitporter sync --repos repo1,repo2     指定仓库同步（适合 CI）\n"
            "  gitporter sync --workers 4             4 线程并行同步\n"
            "  gitporter sync --retry                 只重试上次失败的仓库\n"
            "\n"
            "文档: https://github.com/Adsryen/GitPorter"
        )
    else:
        desc = "GitPorter — Batch Git repo migration & continuous sync tool"
        epilog = (
            "Quick Start:\n"
            "  1. cp config.yml.example config.yml   Copy config template\n"
            "  2. gitporter config --validate         Validate config\n"
            "  3. gitporter sync --dry-run            Preview without executing\n"
            "  4. gitporter sync                      Start syncing\n"
            "\n"
            "Common Usage:\n"
            "  gitporter list --search keyword        Search repos by keyword\n"
            "  gitporter list --status                Show sync status\n"
            "  gitporter sync --select                Interactively pick repos\n"
            "  gitporter sync --repos repo1,repo2     Specify repos (for CI)\n"
            "  gitporter sync --workers 4             Parallel sync with 4 workers\n"
            "  gitporter sync --retry                 Retry only failed repos\n"
            "\n"
            "Docs: https://github.com/Adsryen/GitPorter"
        )

    parser = argparse.ArgumentParser(
        prog="gitporter",
        description=desc,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=epilog,
    )
    parser.add_argument("-c", "--config", dest="cfg_file", default="./config.yml",
                        help="config file (default: ./config.yml)")

    # ── sync ──
    sync_help = "执行仓库同步（自动判断全量/增量）" if zh else "Sync repos (auto full/incremental)"
    sync_parser = subparsers_add = parser.add_subparsers(dest="command")
    sync_parser = parser.add_subparsers(dest="command")

    return parser


def main():
    zh = _is_chinese()

    parser = argparse.ArgumentParser(
        prog="gitporter",
        description="GitPorter — Git 代码仓批量迁移 & 持续同步工具" if zh else
                    "GitPorter — Batch Git repo migration & continuous sync tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "快速开始:\n"
            "  1. cp config.yml.example config.yml   复制配置模板\n"
            "  2. gitporter config --validate         校验配置是否正确\n"
            "  3. gitporter sync --dry-run            预演，确认无误后执行\n"
            "  4. gitporter sync                      开始同步\n"
            "\n"
            "常用场景:\n"
            "  gitporter list --search keyword        按关键词搜索仓库\n"
            "  gitporter list --status                查看哪些仓库已同步\n"
            "  gitporter sync --select                交互式挑选仓库同步\n"
            "  gitporter sync --repos repo1,repo2     指定仓库同步（适合 CI）\n"
            "  gitporter sync --workers 4             4 线程并行同步\n"
            "  gitporter sync --retry                 只重试上次失败的仓库\n"
            "\n"
            "文档: https://github.com/Adsryen/GitPorter"
        ) if zh else (
            "Quick Start:\n"
            "  1. cp config.yml.example config.yml   Copy config template\n"
            "  2. gitporter config --validate         Validate config\n"
            "  3. gitporter sync --dry-run            Preview without executing\n"
            "  4. gitporter sync                      Start syncing\n"
            "\n"
            "Common Usage:\n"
            "  gitporter list --search keyword        Search repos by keyword\n"
            "  gitporter list --status                Show sync status\n"
            "  gitporter sync --select                Interactively pick repos\n"
            "  gitporter sync --repos repo1,repo2     Specify repos (for CI)\n"
            "  gitporter sync --workers 4             Parallel sync with 4 workers\n"
            "  gitporter sync --retry                 Retry only failed repos\n"
            "\n"
            "Docs: https://github.com/Adsryen/GitPorter"
        ),
    )
    parser.add_argument("-c", "--config", dest="cfg_file", default="./config.yml",
                        help="config file (default: ./config.yml)")

    subparsers = parser.add_subparsers(dest="command")

    # ── sync ──
    sync_parser = subparsers.add_parser("sync",
        help="执行仓库同步" if zh else "Sync repositories")
    sync_parser.add_argument("-c", "--config", dest="cfg_file", default="./config.yml")
    sync_parser.add_argument("--dry-run", action="store_true",
        help="预演模式，不实际执行" if zh else "Preview without executing")
    sync_parser.add_argument("-y", "--yes", action="store_true",
        help="跳过确认提示" if zh else "Skip confirmation prompt")
    sync_parser.add_argument("--force-reclone", action="store_true",
        help="强制全量重新克隆" if zh else "Force full re-clone")
    sync_parser.add_argument("--select", action="store_true",
        help="交互式选择仓库（支持搜索、范围）" if zh else "Interactively select repos")
    sync_parser.add_argument("--retry", action="store_true",
        help="只重试上次失败的仓库" if zh else "Retry only failed repos")
    sync_parser.add_argument("--repos", dest="repos_pattern", default="",
        help="指定仓库名，逗号分隔" if zh else "Comma-separated repo names")
    sync_parser.add_argument("--workers", type=int, default=1,
        help="并行同步线程数（默认 1）" if zh else "Parallel workers (default: 1)")

    # ── list ──
    list_parser = subparsers.add_parser("list",
        help="列出源端仓库" if zh else "List source repositories")
    list_parser.add_argument("-c", "--config", dest="cfg_file", default="./config.yml")
    list_parser.add_argument("--filter", dest="filter_pattern", default="",
        help="通配符过滤（如 test_*）" if zh else "Glob filter (e.g. test_*)")
    list_parser.add_argument("--exclude", dest="exclude_pattern", default="",
        help="通配符排除（如 archived-*）" if zh else "Glob exclude (e.g. archived-*)")
    list_parser.add_argument("--status", action="store_true",
        help="显示同步状态" if zh else "Show sync status")
    list_parser.add_argument("--limit", type=int, default=0,
        help="只显示前 N 个仓库" if zh else "Show first N repos only")
    list_parser.add_argument("--search", dest="search_keyword", default="",
        help="关键词搜索（匹配名称和描述）" if zh else "Keyword search (name + description)")

    # ── config ──
    config_parser = subparsers.add_parser("config",
        help="配置文件管理" if zh else "Config management")
    config_parser.add_argument("-c", "--config", dest="cfg_file", default="./config.yml",
        help="config file (default: ./config.yml)")
    config_parser.add_argument("-o", "--output", dest="output", default="./config.yml")
    config_parser.add_argument("--show", action="store_true",
        help="查看配置（token 脱敏）" if zh else "Show config (tokens masked)")
    config_parser.add_argument("--validate", action="store_true",
        help="校验配置" if zh else "Validate config")

    args = parser.parse_args()

    if args.command is None:
        precheck()
        from gitporter.sync import run_sync
        run_sync(args.cfg_file)
        return

    if args.command == "sync":
        precheck()
        from gitporter.sync import run_sync
        run_sync(args.cfg_file, dry_run=args.dry_run, yes=args.yes,
                 force_reclone=args.force_reclone, select=args.select,
                 retry=args.retry, repos_pattern=args.repos_pattern,
                 workers=args.workers)

    elif args.command == "list":
        from gitporter.commands.list_cmd import run_list
        run_list(args.cfg_file, filter_pattern=args.filter_pattern,
                 exclude_pattern=args.exclude_pattern, status=args.status,
                 limit=args.limit, search_keyword=args.search_keyword)

    elif args.command == "config":
        from gitporter.commands.config_cmd import run_config
        if args.validate:
            from gitporter.commands.config_cmd import run_validate
            run_validate(args.cfg_file)
        else:
            run_config(args.output, show=args.show, cfg_file=args.cfg_file)


if __name__ == "__main__":
    main()
