# Gigrator CLI 增强计划

## 背景

当前所有功能压在一个命令 `gigrator -c config.yml` 里，用户需要手写 YAML 配置、无法预览同步结果、无进度反馈。
目标：降低使用门槛，让无经验用户也能独立完成配置和同步。

---

## TODO 列表

### 1. `gigrator config` — 交互式生成/修改配置

**目标**：用户不用手写 YAML，通过问答引导完成配置。

**实现方案**：
- 新增命令：`gigrator config`（无参数时进入交互向导）
- `gigrator config --show` 查看当前配置（脱敏显示 token）
- 交互流程：选源平台 → 填认证信息 → 选目标平台 → 填认证信息 → 确认生成
- 支持修改已有配置：检测到 config.yml 已存在时询问是新建还是编辑
- **不需要额外依赖**，用 `input()` 实现，简单够用

**涉及文件**：
- 新建 `gigrator/commands/config_cmd.py`
- 修改 `gigrator/cli.py` — 添加子命令路由

---

### 2. `gigrator list` — 列出仓库，支持过滤

**目标**：配完后先确认"我有哪些仓库"，不用真的跑同步。

**实现方案**：
- 新增命令：`gigrator list [-c config.yml]`
- `--filter "test_*"` — 只显示匹配的仓库（复用 `fnmatch`）
- `--exclude "archived-*"` — 排除匹配的仓库（复用 `exclude_repos` 逻辑）
- `--target` — 同时显示目标端已有仓库（标记哪些会跳过）
- 输出表格格式：序号、仓库名、是否已存在于目标

**涉及文件**：
- 新建 `gigrator/commands/list_cmd.py`
- 复用 `config.py` 的 `prepare_migrate` 逻辑（拆出公共部分）

---

### 3. `gigrator sync --dry-run` — 预览模式 + 确认提示

**目标**：执行前告诉用户"我会做什么"，不真的动任何东西。

**实现方案**：
- `gigrator sync [-c config.yml]` — 正常同步（兼容原来的 `gigrator -c config.yml`）
- `gigrator sync --dry-run` — 只打印计划，不执行
- `--yes` / `-y` — 跳过确认直接执行（适合 CI 场景）
- 预览输出：
  ```
  将同步 428 个仓库（已排除 6 个）:
    repo_a, repo_b, repo_c ...
  跳过的仓库（匹配 exclude_repos）:
    test_foo (test_*), archived-bar (archived-*)
  确认执行？[y/N]
  ```
- 无 `--yes` 且非 TTY 时（CI 环境）直接跳过确认

**涉及文件**：
- 修改 `gigrator/sync.py` — 添加 dry-run 逻辑
- 修改 `gigrator/cli.py` — 添加 --dry-run / --yes 参数

---

### 4. 进度条 — 同步过程可视化

**目标**：500 个仓库同步时能看到进度，知道跑到第几个、当前是哪个。

**实现方案**：
- 新增依赖：`rich`（终端渲染库，支持进度条、表格、颜色）
- 同步时显示：`Syncing repos: ████████░░░░░░░░ 42/428 [repo_name]`
- 成功/失败用颜色区分（绿色/红色）
- 非 TTY 环境（CI/管道）自动降级为普通 print 输出

**涉及文件**：
- 修改 `pyproject.toml` — 添加 `rich` 依赖
- 修改 `gigrator/sync.py` — 进度条集成

---

## 子命令结构设计

```
gigrator config              # 交互式生成配置
gigrator config --show       # 查看当前配置（脱敏）
gigrator list                # 列出源端所有仓库
gigrator list --filter "x"   # 过滤显示
gigrator list --exclude "x"  # 排除显示
gigrator sync                # 执行同步（兼容 gigrator -c config.yml）
gigrator sync --dry-run      # 预览，不执行
gigrator sync --yes          # 跳过确认
gigrator -c /path/to/config  # 指定配置文件（所有子命令通用）
```

向后兼容：`gigrator -c config.yml`（无子命令）等价于 `gigrator sync -c config.yml`。

## 实施顺序

1. ~~**项目结构重构** — 文件拆分，解耦~~ ✅ 已完成
2. **`config` 子命令** — 降低首次使用门槛
3. **`list` 子命令** — 让用户确认仓库列表
4. **`sync --dry-run`** — 安全预览
5. **进度条** — 添加 `rich` 依赖，替换 sync 中的 print 输出

## 新增依赖

```toml
dependencies = [
    "pyyaml>=6.0.3",
    "requests>=2.32.5",
    "rich>=13.0",        # 进度条 + 表格 + 颜色输出
]
```
