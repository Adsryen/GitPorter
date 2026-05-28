"""
author: Adsryen <prl1594959462@gmail.com>
link: https://github.com/Adsryen/GitPorter.git
"""
import argparse
from gitporter.util import git_version


def precheck():
    git_version()


def main():
    parser = argparse.ArgumentParser(
        description="GitPorter - Git repositories migration tool.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples:\n"
               "  gitporter sync -c config.yml\n"
               "  gitporter sync --dry-run\n"
               "  gitporter list\n"
               "  gitporter config\n"
    )
    parser.add_argument("-c", "--config", dest="cfg_file", default="./config.yml",
                        help="config file (default: ./config.yml)")

    subparsers = parser.add_subparsers(dest="command")

    sync_parser = subparsers.add_parser("sync", help="Sync repositories from source to target")
    sync_parser.add_argument("-c", "--config", dest="cfg_file", default="./config.yml")
    sync_parser.add_argument("--dry-run", action="store_true",
                             help="Preview what would be synced without executing")
    sync_parser.add_argument("-y", "--yes", action="store_true",
                             help="Skip confirmation prompt")
    sync_parser.add_argument("--force-reclone", action="store_true",
                             help="Force full re-clone even if local cache exists")

    list_parser = subparsers.add_parser("list", help="List repositories from source")
    list_parser.add_argument("-c", "--config", dest="cfg_file", default="./config.yml")
    list_parser.add_argument("--filter", dest="filter_pattern", default="",
                             help="Only show repos matching pattern (e.g. 'test_*')")
    list_parser.add_argument("--exclude", dest="exclude_pattern", default="",
                             help="Exclude repos matching pattern (e.g. 'archived-*')")

    config_parser = subparsers.add_parser("config", help="Interactively generate config file")
    config_parser.add_argument("-o", "--output", dest="output", default="./config.yml")
    config_parser.add_argument("--show", action="store_true",
                               help="Show current config (tokens masked)")

    args = parser.parse_args()

    if args.command is None:
        precheck()
        from gitporter.sync import run_sync
        run_sync(args.cfg_file)
        return

    if args.command == "sync":
        precheck()
        from gitporter.sync import run_sync
        run_sync(args.cfg_file, dry_run=args.dry_run, yes=args.yes, force_reclone=args.force_reclone)

    elif args.command == "list":
        from gitporter.commands.list_cmd import run_list
        run_list(args.cfg_file, filter_pattern=args.filter_pattern, exclude_pattern=args.exclude_pattern)

    elif args.command == "config":
        from gitporter.commands.config_cmd import run_config
        run_config(args.output, show=args.show)


if __name__ == "__main__":
    main()
