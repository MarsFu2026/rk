# Troubleshooting: Rakuten AI Gateway 在 GitHub Runner 中无法访问

## 错误现象

```
httpcore.ConnectTimeout: timed out
anthropic.APITimeoutError: Request timed out or interrupted.
```

错误发生在 `call_claude()` 阶段，即向 `api.ai.public.rakuten-it.com` 发起请求时。

---

## 判断依据

| 步骤 | 结果 | 说明 |
|------|------|------|
| 抓取 gist.github.com 文档 | ✅ 成功 | Runner 网络本身正常 |
| 获取 api.github.com PR diff | ✅ 成功 | GitHub API 可达 |
| 连接 api.ai.public.rakuten-it.com | ❌ ConnectTimeout | 在 TCP 层即超时 |

外部网络正常，仅 Rakuten Gateway 超时，说明是访问限制而非 Runner 网络故障。

---

## 根本原因

`api.ai.public.rakuten-it.com` 虽含 `public`，但属于 `rakuten-it.com` 内部 IT 域，极有可能：

- 要求从公司 VPN / 内网访问
- 或设有 IP 白名单，只允许 Rakuten 出口 IP

GitHub 托管 Runner 的 IP 不在白名单内，TCP 连接请求被丢弃，等到超时。

---

## 解决方案

### 方案 A：Self-hosted Runner（推荐）

将 Runner 部署在能访问 Rakuten Gateway 的内网机器上：

```yaml
jobs:
  design-doc-review:
    runs-on: self-hosted   # 改为自托管 Runner
```

优点：保留 Rakuten 统一管控和 OTEL 遥测能力，网络问题根本解决。

### 方案 B：改用 Anthropic 官方 API

```yaml
# workflow YAML
env:
  ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
```

```python
# agent/review.py
client = anthropic.Anthropic()  # 自动读取 ANTHROPIC_API_KEY
message = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    ...
)
```

代价：失去 Rakuten 统一管控和遥测，但功能等价，可在公网 Runner 上直接运行。
