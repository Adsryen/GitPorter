"""
author: Adsryen <prl1594959462@gmail.com>
link: https://github.com/Adsryen/GitPorter.git
"""
from gitporter.config import load_config, prepare_migrate


def run_sync(cfg_file: str):
    cfg = load_config(cfg_file)
    from_git, to_git, repos = prepare_migrate(cfg)

    success_count = 0
    fail_count = 0
    for repo in repos:
        repo_name = repo["name"]
        try:
            repo_dir, clone_err = from_git.clone_repo(repo_name, repo_owner=repo.get("owner", ""))
            if not repo_dir:
                print(f"[FAIL] clone {repo_name} failed: {clone_err}")
                fail_count += 1
                continue

            has_create = to_git.create_repo(name=repo_name, desc=repo.get("desc", ""), is_private=repo.get("is_private", True))
            if not has_create:
                if to_git.is_repo_existed(repo_name):
                    print(f"[WARN] create {repo_name} skipped: repo already exists on target")
                else:
                    print(f"[FAIL] create {repo_name} failed: API returned non-success status")
                fail_count += 1
                continue

            ok, push_err = to_git.push_repo(repo_name, repo_dir)
            if ok:
                print(f"[OK]   push {repo_name} success")
                success_count += 1
            else:
                print(f"[FAIL] push {repo_name} failed: {push_err}")
                fail_count += 1
        except Exception as e:
            print(f"[FAIL] {repo_name} failed: {e}")
            fail_count += 1

    print(f"\nMigration finished: {success_count} succeeded, {fail_count} failed, {len(repos)} total")
