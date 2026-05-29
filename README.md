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

也可以直接复制 [config.yml](./config.yml) 手动编辑。

### 2. 查看配置（可选，token 自动脱敏）

```bash
gitporter config --show
```

### 3. 预览将要同步的仓库

```bash
gitporter list
gitporter list --filter "my-*"       # 只看 my- 开头的仓库
gitporter list --exclude "archived-*" # 排除 archived- 开头的仓库
```

### 4. 预演一遍，不实际执行

```bash
gitporter sync --dry-run
```

### 5. 执行同步

```bash
gitporter sync           # 交互确认后执行
gitporter sync -y        # 跳过确认直接执行（适合脚本/CI）
```

> 首次运行全量克隆，后续自动切换为增量 fetch，无需手动区分。

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
gitporter config                    生成/查看配置文件
gitporter config --show             查看当前配置（token 脱敏显示）
gitporter config -o /path/to/cfg    指定输出路径

gitporter list                      列出源端所有仓库
gitporter list --filter "pattern"   只显示匹配的仓库
gitporter list --exclude "pattern"  排除匹配的仓库

gitporter sync                      执行同步（自动判断全量/增量）
gitporter sync --dry-run            预演，不实际执行
gitporter sync -y                   跳过确认
gitporter sync --force-reclone      强制全量重新克隆（忽略本地缓存）

所有命令均支持 -c 指定配置文件路径：
gitporter sync -c /path/to/config.yml
```

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

- **增量同步**：本地缓存已存在时自动切换为 `git fetch`，首次全量、后续增量，无需手动区分
- **子命令架构**：新增 `config`、`list`、`sync` 子命令，降低使用门槛
- **交互式配置**：`gitporter config` 引导式生成配置文件，无需手写 YAML
- **dry-run 预演**：执行前可预览将要同步的仓库列表，安全可控
- **进度条**：同步过程实时显示进度、当前仓库、耗时
- **仓库过滤**：`exclude_repos` 支持通配符批量排除仓库
- **参数可配置**：`clone_args`、`push_args` 支持自定义 git 参数
- **错误信息优化**：失败时输出具体原因，单个失败不影响整体
- **项目结构重构**：模块解耦，便于维护和扩展

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
