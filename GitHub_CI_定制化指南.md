# GitHub 定制化 CI 流程指南

## 概述

GitHub Actions 是 GitHub 内置的 CI/CD 平台，通过在仓库中编写 YAML 配置文件，定义自动化流程（Workflow），在代码推送、PR 提交等事件触发时自动执行构建、测试、部署等任务。

---

## 核心概念

```
Workflow（工作流）
  └── Job（任务，可并行）
        └── Step（步骤，顺序执行）
              ├── uses: 引用现成 Action
              └── run:  执行 Shell 命令
```

| 概念 | 说明 |
|---|---|
| **Workflow** | 一个完整的自动化流程，对应一个 `.yml` 文件 |
| **Event** | 触发 Workflow 的事件，如 `push`、`pull_request`、`schedule` |
| **Job** | Workflow 中的并行任务单元，每个 Job 运行在独立的虚拟机上 |
| **Step** | Job 内的顺序执行步骤，可以是脚本或 Action |
| **Action** | 可复用的步骤模块，来自官方市场或自定义 |
| **Runner** | 执行 Job 的虚拟机，官方提供 Ubuntu / macOS / Windows |

---

## 定制化 CI 的完整步骤

### 第一步：创建 Workflow 文件

在仓库根目录创建文件路径：

```
.github/workflows/<workflow-name>.yml
```

一个仓库可以有多个 workflow 文件，互相独立。

---

### 第二步：定义触发事件（on）

```yaml
on:
  push:
    branches: [main, develop]        # 推送到指定分支时触发
  pull_request:
    types: [opened, synchronize]     # PR 创建或更新时触发
  schedule:
    - cron: '0 9 * * 1'             # 定时触发（每周一 9:00 UTC）
  workflow_dispatch:                 # 支持手动触发
```

常用事件：

| 事件 | 触发时机 |
|---|---|
| `push` | 代码推送 |
| `pull_request` | PR 创建/更新/关闭 |
| `schedule` | 定时（cron 表达式） |
| `workflow_dispatch` | 手动点击触发 |
| `release` | 发布新版本 |
| `workflow_call` | 被其他 Workflow 调用 |

---

### 第三步：配置运行环境（runs-on）

```yaml
jobs:
  build:
    runs-on: ubuntu-latest     # 官方托管 Runner

  deploy:
    runs-on: self-hosted       # 自托管 Runner（公司内网机器）
```

官方 Runner 选项：`ubuntu-latest`、`macos-latest`、`windows-latest`

---

### 第四步：编写执行步骤（steps）

```yaml
steps:
  # 引用官方 Action：检出代码
  - name: Checkout
    uses: actions/checkout@v4

  # 设置运行环境
  - name: Setup Node.js
    uses: actions/setup-node@v4
    with:
      node-version: '20'

  # 执行自定义 Shell 命令
  - name: Install & Test
    run: |
      npm install
      npm test

  # 条件执行
  - name: Deploy (only on main)
    if: github.ref == 'refs/heads/main'
    run: ./scripts/deploy.sh
```

---

### 第五步：管理敏感信息（Secrets & Variables）

**不要把密钥写在 YAML 文件里**，统一通过仓库设置注入：

```
仓库 → Settings → Secrets and variables → Actions
```

| 类型 | 用途 | 在 YAML 中引用 |
|---|---|---|
| **Secret** | API Key、Token 等敏感值，加密存储，不可查看 | `${{ secrets.MY_KEY }}` |
| **Variable** | 非敏感配置项，可随时查看修改 | `${{ vars.MY_VAR }}` |
| **内置变量** | GitHub 自动注入的上下文信息 | `${{ github.repository }}` |

```yaml
env:
  API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
  THRESHOLD: ${{ vars.SCORE_THRESHOLD || '7' }}   # 支持默认值
```

---

### 第六步：设置 Job 权限（permissions）

默认权限较为保守，需要写操作时必须显式声明：

```yaml
jobs:
  review:
    runs-on: ubuntu-latest
    permissions:
      contents: read           # 读取仓库代码
      pull-requests: write     # 发布 PR 评论
      issues: write            # 写 Issue 评论
      packages: write          # 推送容器镜像
```

---

### 第七步：Job 间依赖与数据传递

```yaml
jobs:
  build:
    runs-on: ubuntu-latest
    outputs:
      version: ${{ steps.get-version.outputs.version }}
    steps:
      - id: get-version
        run: echo "version=1.2.3" >> $GITHUB_OUTPUT

  deploy:
    needs: build                          # 依赖 build 完成后才执行
    runs-on: ubuntu-latest
    steps:
      - run: echo "Deploying ${{ needs.build.outputs.version }}"
```

---

### 第八步：配置分支保护（强制 CI 通过才能合并）

```
仓库 → Settings → Branches → Add branch protection rule
```

关键配置项：

| 选项 | 说明 |
|---|---|
| Require status checks to pass | 指定必须通过的 CI 检查名称 |
| Require branches to be up to date | 合并前必须与目标分支同步 |
| Require pull request reviews | 需要人工 Code Review |
| Restrict who can push | 限制直接推送的人员 |

> CI 检查名称即 job 的 `name` 字段，首次运行后才会出现在搜索列表中。

---

## 常用内置 Action 速查

| Action | 用途 |
|---|---|
| `actions/checkout@v4` | 检出仓库代码 |
| `actions/setup-node@v4` | 配置 Node.js 环境 |
| `actions/setup-python@v5` | 配置 Python 环境 |
| `actions/setup-java@v4` | 配置 Java 环境 |
| `actions/cache@v4` | 缓存依赖，加速构建 |
| `actions/upload-artifact@v4` | 上传构建产物 |
| `actions/download-artifact@v4` | 下载构建产物 |
| `docker/build-push-action@v5` | 构建并推送 Docker 镜像 |

---

## 典型 Workflow 完整示例

```yaml
name: CI Pipeline

on:
  pull_request:
    branches: [main]

jobs:
  test:
    name: Run Tests
    runs-on: ubuntu-latest
    permissions:
      contents: read

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run tests
        run: pytest --tb=short

  lint:
    name: Code Lint
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pip install ruff && ruff check .

  deploy:
    name: Deploy to Staging
    needs: [test, lint]           # test 和 lint 都通过才执行
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    environment: staging          # 关联部署环境，可配置审批人
    steps:
      - uses: actions/checkout@v4
      - run: ./scripts/deploy.sh
        env:
          DEPLOY_TOKEN: ${{ secrets.DEPLOY_TOKEN }}
```

---

## 调试技巧

| 场景 | 方法 |
|---|---|
| 查看运行日志 | 仓库 → Actions → 点击具体 Run → 展开 Step |
| 手动重新触发 | Actions 页面 → Re-run jobs |
| 本地调试 Workflow | 使用 [act](https://github.com/nektos/act) 工具在本地模拟运行 |
| 打印调试信息 | `run: echo "value=${{ vars.MY_VAR }}"` |
| 查看上下文变量 | `run: echo '${{ toJSON(github) }}'` |

---

## 注意事项

- Workflow 文件必须位于 `.github/workflows/` 目录，且在**默认分支**上才会被识别
- Secret 一旦保存无法查看原始值，只能覆盖或删除
- 免费账号每月有 2000 分钟 Runner 时长，超出按量计费
- 自托管 Runner 适合有内网访问需求或需要特殊硬件的场景
- 避免在 `run` 中直接拼接 Secret 到命令字符串（防止日志泄露），应通过 `env` 注入
