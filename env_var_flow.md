# 环境变量传递说明：AWS_BEARER_TOKEN_BEDROCK

## 概述

`AWS_BEARER_TOKEN_BEDROCK` 是 Rakuten AI Gateway 的认证令牌（PAT），通过 GitHub Secrets 机制安全注入到 CI 运行环境中，最终由 Python 代码读取并用于调用 Claude API。

---

## 完整传递链路

```
GitHub Secret（加密存储）
        │  ${{ secrets.RAKUTEN_AI_GATEWAY_TOKEN }}
        ▼
workflow YAML env: 块（Step 级别注入）
        │  注入为 runner 进程环境变量
        ▼
Runner 进程环境变量 AWS_BEARER_TOKEN_BEDROCK=raik-pat-...
        │  os.environ["AWS_BEARER_TOKEN_BEDROCK"]
        ▼
anthropic.Anthropic(api_key=...) → Authorization: Bearer raik-pat-...
        │
        ▼
Rakuten AI Gateway → Claude
```

---

## 各环节详解

### 第一环：GitHub Secret 存储

Token 以加密形式存储在 GitHub 仓库设置中：

```
仓库 → Settings → Secrets and variables → Actions → Secrets
```

| Secret 名称 | 说明 |
|-------------|------|
| `RAKUTEN_AI_GATEWAY_TOKEN` | Rakuten 分配的个人访问令牌（`raik-pat-...`） |

Secret 特性：
- 加密存储，任何人（包括仓库所有者）均无法在界面查看原始值
- 在 Actions 运行日志中自动打码（显示为 `***`）
- 可随时覆盖更新，无需修改代码

---

### 第二环：Workflow YAML 注入

`.github/workflows/design-doc-review.yml` 中，通过 `env:` 块将 Secret 映射为环境变量：

```yaml
- name: Run Design Doc Review Agent
  env:
    AWS_BEARER_TOKEN_BEDROCK: ${{ secrets.RAKUTEN_AI_GATEWAY_TOKEN }}
  run: python agent/review.py
```

关键点：
- `${{ secrets.RAKUTEN_AI_GATEWAY_TOKEN }}` 是 GitHub Actions 表达式，GitHub 在启动该 Step 前自动解密并注入
- `env:` 写在 Step 级别，**仅对 `python agent/review.py` 这一个子进程生效**，其他 Step 无法访问，实现最小权限隔离

---

### 第三环：Python 代码读取

`agent/review.py` 通过标准库直接读取：

```python
client = anthropic.Anthropic(
    base_url=os.environ["ANTHROPIC_BEDROCK_BASE_URL"],
    api_key=os.environ["AWS_BEARER_TOKEN_BEDROCK"],  # ← 此处读取
)
```

`api_key` 会被 SDK 自动转换为 HTTP 请求头：

```
Authorization: Bearer raik-pat-...
```

---

## 命名说明

| 名称 | 层级 | 说明 |
|------|------|------|
| `RAKUTEN_AI_GATEWAY_TOKEN` | GitHub Secret 名 | 存储在 GitHub 的 Secret 标识符 |
| `AWS_BEARER_TOKEN_BEDROCK` | 环境变量名 | Runner 进程中的变量名，由 Workflow 定义 |

两者是**同一个值的不同名称**，通过 YAML 映射关联：
```yaml
AWS_BEARER_TOKEN_BEDROCK: ${{ secrets.RAKUTEN_AI_GATEWAY_TOKEN }}
```

`AWS_BEARER_TOKEN_BEDROCK` 这个名称来自 Anthropic SDK 对 Bedrock 认证的约定，即使现在改用标准 `Anthropic` 客户端，环境变量名保持不变以减少改动。

---

## 本地测试时的设置方式

本地运行时没有 GitHub Secrets，需手动 export：

```bash
export ANTHROPIC_BEDROCK_BASE_URL=https://api.ai.public.rakuten-it.com/claude-code-aws-bedrock/v1
export AWS_BEARER_TOKEN_BEDROCK=raik-pat-<your-token>
export GITHUB_TOKEN=<your-github-pat>
export PR_NUMBER=1
export REPO_FULL_NAME=marsfu2009/rk
export SCORE_THRESHOLD=7

python agent/review.py
```
