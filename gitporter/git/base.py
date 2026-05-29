"""
author: Adsryen <prl1594959462@gmail.com>
link: https://github.com/Adsryen/GitPorter.git
"""
import os
import re
import shutil
import subprocess

from gitporter.util import mask_auth_url

# git --progress 输出的噪声行，用于过滤只保留真正的错误信息
_GIT_PROGRESS_RE = re.compile(
    r"^(Enumerating objects|Counting objects|Compressing objects|"
    r"Writing objects|Receiving objects|Resolving deltas|"
    r"Delta compression|remote:|Total |pack-reused|Everything up-to-date|"
    r"\d+%|.*\d+/\d+\))", re.IGNORECASE
)


def _extract_git_error(stderr: str) -> str:
    """从 git stderr 中提取真正的错误信息，过滤掉进度输出。"""
    lines = stderr.strip().splitlines()
    error_lines = [line for line in lines if line.strip() and not _GIT_PROGRESS_RE.match(line.strip())]
    return "\n".join(error_lines) if error_lines else stderr.strip()


class Git:
    provider = ""
    username = ""
    token = ""
    token_user = ""
    base_api = ""
    ssh_prefix = ""
    https_prefix = ""
    use_https = False
    headers = {}

    def __init__(self, config: dict):
        self.provider = config.get("provider", "").lower()
        if self.provider == "gogs":
            self.provider = "gitea"
        if not self.provider:
            raise ValueError("Invalid provider")

        self.username = config.get("username", "")
        # if not self.username:
        #     raise ValueError("Invalid username")

        self.token = config.get("token", "")
        if not self.token:
            raise ValueError("Invalid token")
        self.token_user = config.get("token_user", self.username)

        self.ssh_prefix = config.get("ssh_prefix", "")
        if self.ssh_prefix.endswith(":"):
            self.ssh_prefix = self.ssh_prefix.rstrip(":")

        self.https_prefix = config.get("https_prefix", "")
        if self.https_prefix.endswith("/"):
            self.https_prefix = self.https_prefix.rstrip("/")
        self.https_prefix_auth = ""
        if self.https_prefix:
            self.https_prefix_auth = self._https_prefix_auth()

        self.use_https = config.get("use_https", False)
        if self.use_https and not self.https_prefix:
            raise ValueError("https_prefix is required when use_https is True")

        self.base_api = config.get("base_api", "")
        if self.base_api:
            if not re.match(r"^http(s)?://.+$", self.base_api):
                raise ValueError("Invalid base_api")
            self.base_api = self.base_api.rstrip("/")

        self.clone_dir = config.get("clone_dir", "")
        if not self.clone_dir:
            self.clone_dir = os.path.join(os.getcwd(),
                                          ".gitporter",
                                          self.provider)
        else:
            self.clone_dir = os.path.join(self.clone_dir,
                                          self.provider)
        os.makedirs(self.clone_dir, exist_ok=True)

        # git clone 额外参数，例如 ["--depth", "1", "--filter=blob:none"]
        self.clone_args = config.get("clone_args", [])
        # git push 额外参数，例如 ["--force"]
        self.push_args = config.get("push_args", [])

    def _https_prefix_auth(self) -> str:
        parts = self.https_prefix.split("://")
        schema = parts[0]
        domain = parts[1]
        return f"{schema}://{self.token_user}:{self.token}@{domain}"

    def clone_repo(self, repo_name: str, repo_owner: str = "", force_reclone: bool = False) -> tuple:
        """Returns (repo_dir, error_msg, action).

        action 为 'clone' 或 'fetch'，表示实际执行的操作。
        成功时 error_msg 为空，失败时 repo_dir 为 None。
        若本地 bare 仓库已存在且 force_reclone=False，自动切换为 fetch 增量更新。
        """
        if not repo_owner:
            repo_owner = self.username

        repo_path = f"{repo_owner}/{repo_name}"
        clone_dir = os.path.join(self.clone_dir, repo_owner)
        os.makedirs(clone_dir, exist_ok=True)

        remote_addr = f"{self.ssh_prefix}:{repo_path}.git"
        if self.use_https:
            remote_addr = f"{self.https_prefix_auth}/{repo_path}.git"

        repo_dir = os.path.join(clone_dir, repo_name + ".git")

        # 本地已有缓存且不强制重新克隆 → 增量 fetch
        if os.path.exists(repo_dir) and not force_reclone:
            repo_dir, error_msg = self._fetch_repo(repo_dir, remote_addr)
            return repo_dir, error_msg, "fetch"

        # 首次或强制重新克隆
        if os.path.exists(repo_dir):
            shutil.rmtree(repo_dir)

        clone_cmd = ["git", "clone", "--bare", "--progress"] + self.clone_args + [remote_addr]
        ret = subprocess.run(args=clone_cmd,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE,
                             encoding="utf-8",
                             cwd=clone_dir)
        if ret.returncode == 0:
            return repo_dir, "", "clone"

        error_msg = _extract_git_error(ret.stderr) if ret.stderr else f"git clone exited with code {ret.returncode}"
        return None, mask_auth_url(error_msg), "clone"

    def _fetch_repo(self, repo_dir: str, remote_addr: str) -> tuple:
        """对已有 bare 仓库执行增量 fetch。Returns (repo_dir, error_msg)."""
        fetch_cmd = ["git", "fetch", "--prune", "--progress", remote_addr, "+refs/*:refs/*"]
        ret = subprocess.run(args=fetch_cmd,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE,
                             encoding="utf-8",
                             cwd=repo_dir)
        if ret.returncode == 0:
            return repo_dir, ""

        error_msg = _extract_git_error(ret.stderr) if ret.stderr else f"git fetch exited with code {ret.returncode}"
        return None, mask_auth_url(error_msg)

    def push_repo(self, repo_name: str, repo_dir: str, repo_owner: str = "") -> tuple:
        """Returns (success, error_msg). On success error_msg is empty."""
        if not repo_owner:
            repo_owner = self.username
        remote_addr = f"{self.ssh_prefix}:{repo_owner}/{repo_name}.git"

        if self.use_https:
            remote_addr = f"{self.https_prefix_auth}/{repo_owner}/{repo_name}.git"

        push_cmd = ["git", "push", "--mirror", "--progress"] + self.push_args + [remote_addr]
        ret = subprocess.run(args=push_cmd,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE,
                             encoding="utf-8",
                             cwd=repo_dir)
        if ret.returncode == 0:
            return True, ""

        error_msg = _extract_git_error(ret.stderr) if ret.stderr else f"git push exited with code {ret.returncode}"
        return False, mask_auth_url(error_msg)

    def list_repos(self) -> list:
        raise NotImplementedError

    def create_repo(self, name: str, desc: str, is_private: bool) -> bool:
        raise NotImplementedError

    def is_repo_existed(self, repo_name: str) -> bool:
        raise NotImplementedError
