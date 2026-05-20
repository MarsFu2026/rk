# GitHub CI 运行原理

## 整体流程

```
开发者提 PR
    ↓
GitHub 检测到事件（push / pull_request / ...）
    ↓
GitHub 读取 .github/workflows/*.yml
    ↓
分配 Runner（运行机器）
    ↓
Runner 按步骤顺序执行 Job
    ↓
每个 Step 的结果上报给 GitHub
    ↓
CI 状态显示在 PR 页面（绿/红）
```

---

## 运行环境是怎么来的

### 1. Runner 是什么

Runner 是实际执行 CI 任务的机器。有两种：

| 类型 | 说明 |
|---|---|
| GitHub-hosted Runner | GitHub 官方提供，免费额度内按分钟计费 |
| Self-hosted Runner | 自己的服务器注册到 GitHub，完全自管 |

workflow 中用 `runs-on` 指定：

```yaml
jobs:
  my-job:
    runs-on: ubuntu-latest   # 使用 GitHub 官方 Ubuntu 机器
```

常用选项：`ubuntu-latest`、`macos-latest`、`windows-latest`。

---

### 2. GitHub-hosted Runner 的运行机制

每次触发 CI，GitHub 都会：

1. **新建一个全新的虚拟机**（每次都是干净环境，互不影响）
2. 将仓库代码 checkout 到虚拟机（`actions/checkout` step 做这件事）
3. 按 workflow 定义的步骤顺序执行
4. **执行完毕后销毁虚拟机**

这意味着：
- 每次运行都从零开始，没有上次的残留
- 机器本身预装了大量工具（Python、Node、Java、Docker 等）
- 工作目录默认在 `/home/runner/work/<repo>/<repo>/`

---

### 3. 环境变量的注入方式

CI 脚本需要的密钥和配置，通过以下几种方式注入：

#### Secrets（加密，适合 token/密码）

在 GitHub 仓库 Settings → Secrets 中配置，workflow 中引用：

```yaml
env:
  MY_TOKEN: ${{ secrets.MY_SECRET_NAME }}
```

- 值在日志中自动屏蔽，不会明文显示
- 只能在同仓库的 workflow 中使用（fork 的 PR 默认无法访问）

#### Variables（明文，适合非敏感配置）

在 Settings → Variables 中配置，workflow 中引用：

```yaml
env:
  THRESHOLD: ${{ vars.SCORE_THRESHOLD }}
```

#### GitHub 内置变量

GitHub 自动提供一批上下文变量，无需手动配置：

| 变量 | 内容 |
|---|---|
| `secrets.GITHUB_TOKEN` | 自动生成的临时 token，有当前仓库读写权限 |
| `github.repository` | 仓库全名，如 `owner/repo` |
| `github.event.pull_request.number` | 触发本次 CI 的 PR 编号 |
| `github.sha` | 当前 commit 的 SHA |

---

### 4. 本项目的运行环境

以 `design-doc-review.yml` 为例，完整流程：

```
GitHub 检测到 PR 事件
    ↓
分配一台全新 ubuntu-latest 虚拟机
    ↓
Step 1: actions/checkout@v4
  → 把仓库代码 clone 到虚拟机
    ↓
Step 2: actions/setup-python@v5
  → 安装 Python 3.12（机器上可能已有，这一步确保版本正确）
    ↓
Step 3: pip install anthropic requests
  → 在虚拟机上安装 Python 依赖
    ↓
Step 4: python agent/review.py
  → 执行脚本，环境变量由 env 块注入：
      ANTHROPIC_BEDROCK_BASE_URL = （硬编码 URL）
      AWS_BEARER_TOKEN_BEDROCK   = （来自 Secrets）
      GITHUB_TOKEN               = （GitHub 自动提供）
      PR_NUMBER                  = （来自事件上下文）
      REPO_FULL_NAME             = （来自 vars 或事件上下文）
      SCORE_THRESHOLD            = （来自 Variables，默认 7）
    ↓
脚本 exit(0) → CI 绿 / exit(1) → CI 红
    ↓
虚拟机销毁
```

---

## 关键概念速查

| 概念 | 说明 |
|---|---|
| Workflow | `.github/workflows/` 下的 yml 文件，定义整个 CI 流程 |
| Job | Workflow 中的一个并行单元，每个 Job 独占一台 Runner |
| Step | Job 内串行执行的最小单元，可以是 shell 命令或 Action |
| Action | 可复用的 Step 封装，如 `actions/checkout`、`actions/setup-python` |
| Runner | 执行 Job 的虚拟机 |
| Secrets | 加密的敏感配置，如 API token |
| Variables | 明文的非敏感配置，如阈值、开关 |
