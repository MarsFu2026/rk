# 方案 B：多仓库 CI 架构

## 概述

将 `rk` 作为 **CI 工具仓库**，业务代码放在独立的**业务仓库**，两者通过 GitHub Actions 机制连接。`rk` 统一维护 CI 逻辑，各业务仓库按需接入。

---

## 架构关系

```
rk/（CI 工具仓库）                    business-app/（业务仓库）
├── .github/workflows/               ├── src/
│   └── design-doc-review.yml        ├── tests/
├── agent/                           └── .github/workflows/
│   └── review.py                        └── ci.yml  ← 调用 rk 里的 workflow
└── ...
```

---

## 两种连接方式

### 方式一：`workflow_call`（推荐）

将 `rk` 里的 workflow 改造为**可复用模块**，业务仓库直接调用，无需关心实现细节。

**rk 侧** — 改为 `workflow_call` 触发：

```yaml
# rk/.github/workflows/design-doc-review.yml
on:
  workflow_call:
    inputs:
      score_threshold:
        type: number
        default: 7
    secrets:
      ANTHROPIC_API_KEY:
        required: true
```

**业务仓库侧** — 调用 rk 的 workflow：

```yaml
# business-app/.github/workflows/ci.yml
jobs:
  design-review:
    uses: marsfu2009/rk/.github/workflows/design-doc-review.yml@main
    secrets:
      ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
    with:
      score_threshold: 8
```

**优点**：
- 业务仓库只需 3 行 YAML 即可接入
- `rk` 升级逻辑后，所有接入方自动生效
- 支持多个业务仓库同时接入

---

### 方式二：`TARGET_REPO` 变量（当前已支持，开箱即用）

当前 `review.py` 已内置支持，无需修改代码：

```yaml
REPO_FULL_NAME: ${{ vars.TARGET_REPO || github.repository }}
```

在 `rk` 的 Variables 中设置 `TARGET_REPO = owner/business-app`，`rk` 自己的 PR 触发后，Agent 自动去审查目标仓库的 PR。

**配置路径**：`rk` 仓库 → Settings → Secrets and variables → Actions → Variables

| 名称 | 值 |
|---|---|
| `TARGET_REPO` | `owner/business-app` |

**局限**：
- 只能指向单个目标仓库
- 不适合多业务仓库场景

---

## 方式选择建议

| 场景 | 推荐方式 |
|---|---|
| 多个业务仓库都需要接入 Agent | 方式一（`workflow_call`） |
| 只有一个业务仓库 | 方式二（`TARGET_REPO`，无需改动，立即可用） |
| 业务仓库不在同一 GitHub 账号下 | 方式一 + PAT 授权 |

---

## 跨账号授权补充（方式一）

若业务仓库属于不同 GitHub 账号或组织，需额外配置 PAT：

1. 在业务仓库所有者账号下生成 PAT，权限勾选 `repo`
2. 将 PAT 存入 `rk` 的 Secrets：`GH_PAT`
3. 在 workflow 中将 `secrets.GITHUB_TOKEN` 替换为 `secrets.GH_PAT`

---

> 返回方案对比见 [方案选择_单仓库vs多仓库.md](./方案选择_单仓库vs多仓库.md)
