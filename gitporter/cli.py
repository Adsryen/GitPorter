"""
author: Adsryen <prl1594959462@gmail.com>
link: https://github.com/Adsryen/GitPorter.git
"""
from gitporter.util import git_version
from gitporter.sync import run_sync
import argparse


def precheck():
    git_version()


def parse_args():
    parser = argparse.ArgumentParser(
        description="Git repositories migration tool.")
    parser.add_argument("-c", "--config", dest="cfg_file", default="./config.yml",
                        help="config file (default: ./config.yml)")
    args = parser.parse_args()
    return args


def main():
    args = parse_args()
    precheck()
    run_sync(args.cfg_file)


if __name__ == "__main__":
    main()
