"""
author: Adsryen <prl1594959462@gmail.com>
link: https://github.com/Adsryen/GitPorter.git
"""
import subprocess
import sys
import re


def mask_secret(text: str, secret: str) -> str:
    """将 text 中出现的 secret 替换为打码形式。

    保留前 3 位和后 3 位，中间用 **** 替代。
    若 secret 长度不足 6 位或为空则全部打码。
    """
    if not secret:
        return text
    if len(secret) <= 6:
        masked = "****"
    else:
        masked = secret[:3] + "****" + secret[-3:]
    return text.replace(secret, masked)


def mask_auth_url(url: str) -> str:
    """将 URL 中的 user:pass@ 部分打码。

    匹配 https://user:token@domain 形式，token 打码处理。
    """
    return re.sub(
        r"(://)([^:]+):([^@]+)(@)",
        lambda m: f"{m.group(1)}{m.group(2)}:****{m.group(4)}",
        url,
    )


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
