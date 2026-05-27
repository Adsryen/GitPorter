<p align="center">
  <img src="./assets/logo.png" alt="GitPorter Logo" width="160" />
</p>

<h1 align="center">GitPorter</h1>

<p align="center">Git 代码仓批量迁移工具</p>

---

GitPorter 是一个 Git 代码仓批量迁移工具，支持众多流行的代码托管平台，包括 GitHub、码云（Gitee）、GitLab、Gitea、Coding、Gogs、腾讯工蜂，同时可以基于本项目进行拓展其他代码托管平台。

## 支持的平台

- [x] [Gitee](https://gitee.com/)
- [x] [GitLab](https://gitlab.com/)
- [x] [GitHub](https://github.com/)
- [x] [Gitea](https://gitea.io/zh-cn/)
- [x] [Coding](https://coding.net/)
- [x] [Gogs](https://gogs.io/)
- [x] [腾讯工蜂](https://code.tencent.com/)
- [ ] [Bitbucket](https://bitbucket.org/)
- [ ] [云效 Codeup](https://codeup.aliyun.com/)

## 安装

```bash
pip install gitporter
```

或源码安装：

```shell
git clone https://github.com/Adsryen/GitPorter.git
cd GitPorter
make
```

## 使用

### 环境要求

- Git
- Python 3.13+

### 配置文件

参考 [config.yml](./config.yml)

### 运行

```bash
gitporter -c config.yml
```

## 扩展更多平台

基于 `Git` 类实现其他平台的代码仓迁移：

```python
class Git:
    def list_repos(self) -> list:
        raise NotImplementedError

    def create_repo(self, name: str, desc: str, is_private: bool) -> bool:
        raise NotImplementedError

    def is_repo_existed(self, repo_name: str) -> bool:
        raise NotImplementedError
```

## 说明

- 暂不支持迁移至 `Coding`，可从 Coding 迁移至其他 Git 服务器
- 由于 `Coding` 的升级，其基础 API 不再是 `https://coding.net`，而改为 `https://{username}.coding.net`
- 迁移前请确认已在 Git 服务器上添加 SSH Key
- 只能迁移指定用户下的仓库（`{username}/{repo_name}`），不包括参与的或组织的仓库
- 迁移包括 commits、branches 和 tags，不包括 issues、PR 和 wiki

## 相较原项目的改进

本项目 Fork 自 [k8scat/Gigrator](https://github.com/k8scat/Gigrator)，在原项目基础上做了以下优化：

- **项目结构重构**：将原本集中在单文件的逻辑拆分为 `cli.py`（入口）、`sync.py`（同步逻辑）、`git/factory.py`（provider 工厂）等独立模块，降低耦合，便于维护和扩展
- **克隆/推送参数可配置**：支持在配置文件中自定义 `clone_args` 和 `push_args`，满足不同网络环境需求
- **仓库过滤增强**：`exclude_repos` 支持通配符（`*`、`?`），可按模式批量排除仓库
- **错误信息优化**：同步失败时输出更清晰的错误原因，区分 clone / create / push 各阶段
- **migrate 公共配置下沉**：`clone_dir`、`clone_args`、`push_args` 可在 `migrate` 段统一配置，各 provider 可单独覆盖

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
