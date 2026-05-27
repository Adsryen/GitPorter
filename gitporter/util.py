"""
author: Adsryen <prl1594959462@gmail.com>
link: https://github.com/Adsryen/GitPorter.git
"""
import subprocess
import sys


def git_version():
    ret = subprocess.run(args=["git", "--version"],
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE,
                         encoding="utf-8")
    if ret.returncode == 0:
        print(ret.stdout, end='')
    else:
        print(ret.stderr, end='')
        sys.exit(1)
