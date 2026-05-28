# GitPorter 开发计划

## 已完成

1. ~~**项目结构重构** — 文件拆分，解耦~~ ✅
2. ~~**`config` 子命令** — 交互式生成配置，`--show` 脱敏查看~~ ✅
3. ~~**`list` 子命令** — 列出仓库，支持 `--filter` / `--exclude` 过滤~~ ✅
4. ~~**`sync --dry-run`** — 预览模式 + 确认提示~~ ✅
5. ~~**进度条** — rich 进度条，成功/失败颜色区分~~ ✅
6. ~~**增量同步** — 自动判断 clone / fetch，`--force-reclone` 强制重建~~ ✅

---

## 待开发

### 7. 容器化适配

**目标**：提供开箱即用的 Docker 运行方式，用户无需安装 Python 环境，挂载配置文件即可运行。

**实现方案**：

#### Dockerfile
- 基础镜像：`python:3.11-slim`（平衡体积与兼容性）
- 安装系统依赖：`git`
- 安装 Python 依赖：`pip install -r requirements.txt`
- 入口：`ENTRYPOINT ["gitporter"]`，CMD 默认 `["sync"]`
- 工作目录：`/app`，配置文件通过 `-v` 挂载

```dockerfile
FROM python:3.11-slim
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN pip install --no-cache-dir -e .
ENTRYPOINT ["gitporter"]
CMD ["sync", "-y"]
```

#### docker-compose.yml
- 挂载本地 `config.yml` 到容器内 `/app/config.yml`
- 挂载本地缓存目录到容器内 `.gitporter/`（增量同步复用本地缓存）
- 支持通过环境变量覆盖配置（可选）

```yaml
services:
  gitporter:
    build: .
    volumes:
      - ./config.yml:/app/config.yml
      - ./.gitporter:/app/.gitporter
```

#### 运行方式
```bash
# 构建镜像
docker build -t gitporter .

# 一次性同步
docker run --rm -v $(pwd)/config.yml:/app/config.yml gitporter sync -y

# 使用 docker-compose
docker-compose run --rm gitporter

# 定时同步（配合 crontab）
0 2 * * * docker-compose -f /path/to/docker-compose.yml run --rm gitporter
```

**涉及文件**：
- 新建 `Dockerfile`
- 新建 `docker-compose.yml`
- 新建 `.dockerignore`
- 更新 `README.md` — 补充 Docker 使用说明

---

## 命令结构（当前）

```
gitporter config                    交互式生成配置
gitporter config --show             查看当前配置（token 脱敏）
gitporter config -o /path/to/cfg    指定输出路径

gitporter list                      列出源端所有仓库
gitporter list --filter "pattern"   只显示匹配的仓库
gitporter list --exclude "pattern"  排除匹配的仓库

gitporter sync                      执行同步（自动判断全量/增量）
gitporter sync --dry-run            预演，不实际执行
gitporter sync -y                   跳过确认
gitporter sync --force-reclone      强制全量重新克隆

所有命令支持 -c 指定配置文件：
gitporter sync -c /path/to/config.yml
```
