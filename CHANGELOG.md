# Changelog

## [1.0.1] - 2025-05-29

### Added

- `sync --select` 交互式仓库选择器，支持序号/范围/搜索过滤
- `sync --retry` 自动重试上次失败的仓库，失败记录保存到 `.last_failed.json`
- `sync --repos repo1,repo2` 命令行直接指定仓库名，无需交互
- `sync --workers N` 多线程并行同步，缩短大批量迁移时间
- `list --status` 显示同步状态（✓ 已同步 / - 未同步）
- `list --search keyword` 关键词搜索，同时匹配仓库名和描述
- `list --limit N` 只显示前 N 个仓库
- `list` 交互式排序，按 `s` 键循环切换（按名称 / 最近推送 / 最近更新 / 创建时间）
- `config --validate` 三层配置校验（结构 → API 连通 → Git 连通）
- `config.yml.example` 配置模板，含所有 provider 的详细注释
- 同步完成后显示总耗时统计
- 单元测试（34 个测试用例，覆盖核心模块）

### Fixed

- git 命令失败时过滤进度噪声，只显示真正的错误信息
- `sync` 确认提示前显示完整的待同步仓库清单

### Changed

- `.dockerignore` 移至项目根目录（修复 setuptools 多包发现错误）
- CI 升级到 Node.js 24 兼容的 actions 版本
- PyPI 描述完善（classifiers、keywords、项目链接）

## [1.0.0] - 2025-05-29

### Added

- Docker 容器化支持（Dockerfile / docker-compose / config.yml.example）
- CI 多架构构建（amd64 + arm64），自动推送到 GHCR
- PyPI 自动发布（trusted publishing + API token 双模式兼容）
- 运行日志密钥脱敏（git URL、API 响应中的 token 自动打码）
- 云效 Codeup 平台支持矩阵（预留）

### Fixed

- `use_https: true` 时不再要求 `ssh_prefix` 为必填字段

## [0.1.1] - 2025-05-28

### Added

- 初始版本发布
- 支持 GitHub、Gitee、GitLab、Gitea、Gogs、Coding、腾讯工蜂
- `sync` 子命令：全量/增量同步、dry-run、进度条、确认提示
- `list` 子命令：列出仓库、`--filter` / `--exclude` 过滤
- `config` 子命令：交互式生成配置、`--show` 脱敏查看
- 增量同步：自动判断 clone / fetch，`--force-reclone` 强制重建
- `clone_args` / `push_args` 自定义 git 参数
- `exclude_repos` 通配符排除
