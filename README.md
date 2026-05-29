<p align="center">
  <img src="./assets/logo.png" alt="GitPorter Logo" width="160" />
</p>

<h1 align="center">GitPorter</h1>

<p align="center">Git 代码仓批量迁移 & 持续同步工具</p>

<p align="center">
  <a href="https://github.com/Adsryen/GitPorter/blob/master/LICENSE">
    <img src="https://img.shields.io/github/license/Adsryen/GitPorter" />
  </a>
  <a href="https://www.python.org/">
    <img src="https://img.shields.io/badge/python-3.8+-blue" />
  </a>
</p>

---

GitPorter 是一个 Git 代码仓批量迁移工具，支持在 GitHub、Gitee、GitLab、Gitea、Coding、Gogs、腾讯工蜂等平台之间迁移或持续同步仓库。首次运行全量克隆，后续自动增量同步，无需手动区分。

## 支持的平台

| 平台 | 迁移源 | 迁移目标 |
|------|:------:|:--------:|
| [GitHub](https://github.com/) | ✅ | ✅ |
| [Gitee](https://gitee.com/) | ✅ | ✅ |
| [GitLab](https://gitlab.com/) | ✅ | ✅ |
| [Gitea](https://gitea.io/) | ✅ | ✅ |
| [Gogs](https://gogs.io/) | ✅ | ✅ |
| [腾讯工蜂](https://code.tencent.com/) | ✅ | ✅ |
| [Coding](https://coding.net/) | ✅ | ❌ |
| [云效 Codeup](https://codeup.aliyun.com/) | ❌ | ❌ |
| Bitbucket | ❌ | ❌ |

> 迁移内容包括 commits、branches、tags，不包括 issues、PR、wiki。

## 安装

### 方式一：pip 安装

```bash
pip install gitporter
```

### 方式二：源码安装

```bash
git clone https://github.com/Adsryen/GitPorter.git
cd GitPorter
pip install -r requirements.txt
pip install -e .
```

### 方式三：uv 安装（推荐）

```bash
git clone https://github.com/Adsryen/GitPorter.git
cd GitPorter
uv sync
```

### 方式四：Docker

无需安装 Python 环境，只需挂载配置文件即可运行。

**快速开始：**

```bash
# 构建镜像
docker build -t gitporter -f deploy/docker/Dockerfile .

# 执行同步（挂载配置文件和缓存目录）
docker run --rm \
  -v $(pwd)/config.yml:/app/config.yml:ro \
  -v $(pwd)/.gitporter:/app/.gitporter \
  gitporter sync -y
```

**使用 Docker Compose（推荐）：**

```bash
cd deploy/docker
# 将 config.yml.example 复制为配置文件并填入你的 token
cp config.yml.example ../../config.yml
# 执行同步
docker compose run --rm gitporter
```

**常用命令变体：**

```bash
# 列出源端仓库
docker run --rm -v $(pwd)/config.yml:/app/config.yml:ro gitporter list

# 预演模式
docker run --rm -v $(pwd)/config.yml:/app/config.yml:ro gitporter sync --dry-run

# 强制全量重新克隆
docker run --rm \
  -v $(pwd)/config.yml:/app/config.yml:ro \
  -v $(pwd)/.gitporter:/app/.gitporter \
  gitporter sync --force-reclone -y
```

**定时同步（配合 crontab）：**

```cron
0 2 * * * docker compose -f /path/to/deploy/docker/docker-compose.yml run --rm gitporter
```

## 快速开始

### 1. 生成配置文件

```bash
gitporter config
```

按照交互向导填写源平台和目标平台的认证信息，自动生成 `config.yml`。

也可以直接复制 [config.yml.example](./config.yml.example) 手动编辑。

### 2. 查看配置（可选，token 自动脱敏）

```bash
gitporter config --show
```

### 3. 校验配置

```bash
gitporter config --validate    # 结构 → API 连通 → Git 连通 三层校验
```

### 4. 查看仓库列表

```bash
gitporter list                          # 列出所有仓库
gitporter list --filter "my-*"          # 只看 my- 开头的仓库
gitporter list --exclude "archived-*"   # 排除 archived- 开头的仓库
gitporter list --search hugo            # 关键词搜索（匹配仓库名和描述）
gitporter list --limit 20               # 只看前 20 个
gitporter list --status                 # 显示同步状态（✓ 已同步 / - 未同步）
```

交互模式下按 `s` 可切换排序方式（按名称 / 最近推送 / 最近更新 / 创建时间）。

### 5. 预演一遍，不实际执行

```bash
gitporter sync --dry-run
```

### 6. 执行同步

```bash
gitporter sync                      # 交互确认后执行
gitporter sync -y                   # 跳过确认（适合脚本/CI）
gitporter sync --select             # 交互式选择仓库（支持搜索、范围选择）
gitporter sync --repos repo1,repo2  # 命令行直接指定仓库名
gitporter sync --workers 4          # 4 线程并行同步
gitporter sync --retry              # 只重试上次失败的仓库
gitporter sync --force-reclone      # 强制全量重新克隆（忽略本地缓存）
```

## 配置文件说明

```yaml
migrate:
  from: github        # 迁移源（对应下方的 provider 配置 key）
  to: gitee           # 迁移目标
  clone_dir: ""       # 本地缓存目录，默认 .gitporter/

  # 只迁移指定仓库（白名单）
  # repos:
  #   - my-repo-a
  #   - my-repo-b

  # 排除指定仓库（黑名单，支持通配符）
  # exclude_repos:
  #   - test_*          # 排除所有 test_ 开头的仓库
  #   - *_backup        # 排除所有 _backup 结尾的仓库
  #   - archived-*

  # 自定义 git clone / push 参数
  # clone_args:
  #   - "--depth"
  #   - "1"
  # push_args:
  #   - "--force"

github:
  provider: github
  base_api: https://api.github.com/graphql
  https_prefix: https://github.com
  username: "your-username"
  token: "ghp_xxxxxxxxxxxx"
  use_https: true

gitee:
  provider: gitee
  base_api: https://gitee.com/api/v5
  ssh_prefix: git@gitee.com
  https_prefix: https://gitee.com
  username: "your-username"
  token: "your-token"
```

## 命令参考

```
gitporter config                        交互式生成配置文件
gitporter config --show                 查看当前配置（token 脱敏显示）
gitporter config --validate             校验配置（结构 + API 连通 + Git 连通）
gitporter config -c path/to/config.yml  指定配置文件路径

gitporter list                          列出源端所有仓库
gitporter list --filter "pattern"       通配符过滤（* 匹配任意，? 匹配单个）
gitporter list --exclude "pattern"      通配符排除
gitporter list --search keyword         关键词搜索（匹配仓库名和描述）
gitporter list --limit N                只显示前 N 个仓库
gitporter list --status                 显示同步状态（已同步/未同步）
# 交互模式下按 s 切换排序：按名称 → 最近推送 → 最近更新 → 创建时间

gitporter sync                          执行同步（自动判断全量/增量）
gitporter sync --dry-run                预演，不实际执行
gitporter sync -y                       跳过确认
gitporter sync --select                 交互式选择仓库（支持搜索、范围）
gitporter sync --repos repo1,repo2      命令行直接指定仓库名
gitporter sync --workers N              N 线程并行同步
gitporter sync --retry                  只重试上次失败的仓库
gitporter sync --force-reclone          强制全量重新克隆（忽略本地缓存）

所有命令均支持 -c 指定配置文件路径：
gitporter sync -c /path/to/config.yml
```

> 首次运行全量克隆，后续自动切换为增量 fetch，无需手动区分。同步完成后会显示总耗时。

## 注意事项

- 迁移前请确认已在目标 Git 服务器上添加 SSH Key（使用 SSH 模式时）
- 只能迁移指定用户自己的仓库，不包括参与的或组织的仓库
- Coding 暂不支持通过 API 创建仓库，只能作为迁移源

## 扩展更多平台

继承 `Git` 基类并实现以下三个方法即可接入新平台：

```python
from gitporter.git.base import Git

class MyGit(Git):
    def list_repos(self) -> list:
        # 返回 [{"name": "repo", "desc": "", "is_private": True}, ...]
        ...

    def create_repo(self, name: str, desc: str, is_private: bool) -> bool:
        ...

    def is_repo_existed(self, repo_name: str) -> bool:
        ...
```

## 相较原项目的改进

本项目 Fork 自 [k8scat/Gigrator](https://github.com/k8scat/Gigrator)，在原项目基础上做了以下优化：

- **增量同步**：本地缓存已存在时自动切换为 `git fetch`，首次全量、后续增量
- **子命令架构**：`config`、`list`、`sync` 子命令，降低使用门槛
- **交互式配置**：`gitporter config` 引导式生成配置文件
- **配置校验**：`config --validate` 三层校验（结构 → API 连通 → Git 连通）
- **dry-run 预演**：执行前可预览将要同步的仓库列表
- **交互式选择**：`sync --select` 带搜索、排序、范围选择的仓库选择器
- **并发同步**：`sync --workers N` 多线程并行同步
- **失败重试**：`sync --retry` 自动记录并重试失败仓库
- **同步状态**：`list --status` 显示每个仓库的同步状态
- **进度条**：同步过程实时显示进度、当前仓库、耗时
- **密钥脱敏**：运行日志中 token 自动打码，不暴露敏感信息
- **Docker 支持**：Dockerfile / docker-compose / CI 多架构自动构建
- **仓库过滤**：`--filter`、`--exclude`、`--search`、`--repos` 多种过滤方式
- **错误信息优化**：过滤 git 进度噪声，只显示真正的错误信息

## 致谢

感谢 [k8scat](https://github.com/k8scat) 开发并开源了原项目 [Gigrator](https://github.com/k8scat/Gigrator)，本项目在其基础上持续迭代。

<a href="https://github.com/k8scat/Gigrator/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=k8scat/Gigrator" />
</a>

## 贡献者

<a href="https://github.com/Adsryen/GitPorter/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=Adsryen/GitPorter" />
</a>

## 开源协议

[MIT](./LICENSE)
