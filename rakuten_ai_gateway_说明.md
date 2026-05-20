# Rakuten AI Gateway 配置说明

## 配置命令

```bash
echo '{
    "env": {
      "ANTHROPIC_BEDROCK_BASE_URL": "https://api.ai.public.rakuten-it.com/claude-code-aws-bedrock/v1",
      "AWS_BEARER_TOKEN_BEDROCK": "raik-pat-436b1a1c2r10ai9a8aa81c395c13ff210e9c69e1e0ee459a8aa81c395c13ff21",
      "CLAUDE_CODE_USE_BEDROCK": "1",
      "CLAUDE_CODE_SKIP_BEDROCK_AUTH": "1",
      "CLAUDE_CODE_ENABLE_TELEMETRY": "1",
      "OTEL_METRICS_EXPORTER": "otlp",
      "OTEL_LOGS_EXPORTER": "otlp",
      "OTEL_EXPORTER_OTLP_PROTOCOL": "http/protobuf",
      "OTEL_EXPORTER_OTLP_ENDPOINT": "https://api.ai.public.rakuten-it.com/otel",
      "OTEL_EXPORTER_OTLP_HEADERS": "Authorization=raik-pat-436b1a1c2r10ai9a8aa81c395c13ff210e9c69e1e0ee459a8aa81c395c13ff21"
  }
}' > ~/.claude/settings.json
```

### 命令解析

这条 shell 命令做了一件事：**把 JSON 内容写入 Claude Code 的用户级配置文件**。

| 部分 | 作用 |
|------|------|
| `echo '...'` | 将单引号内的字符串输出到标准输出 |
| `>` | 重定向操作符，覆盖写入目标文件（不存在则创建） |
| `~/.claude/settings.json` | Claude Code 启动时自动读取，将 `env` 字段中的键值对注入为环境变量 |

**效果**：执行一次即完成配置，无需手动编辑文件，也无需在每次启动时 `export` 环境变量。

---

## 与直接使用 Anthropic API Key 的区别

### 认证方式对比

| 方面 | 直接 Anthropic API | Rakuten AI Gateway |
|------|-------------------|-------------------|
| Key 格式 | `sk-ant-...` | `raik-pat-...`（Rakuten 自己的 PAT） |
| 环境变量 | `ANTHROPIC_API_KEY` | `AWS_BEARER_TOKEN_BEDROCK` |
| 认证对象 | Anthropic 官方服务 | Rakuten 内部网关 |

### 调用链路

```
直接 API:   你的代码 → api.anthropic.com → Claude
Rakuten:    你的代码 → api.ai.public.rakuten-it.com → AWS Bedrock → Claude
```

---

## 各配置项说明

| 配置项 | 说明 |
|--------|------|
| `ANTHROPIC_BEDROCK_BASE_URL` | 将 Bedrock 协议请求重定向到 Rakuten 网关，而非 AWS 直接端点 |
| `AWS_BEARER_TOKEN_BEDROCK` | Rakuten 分配的个人访问令牌（PAT），用于网关认证 |
| `CLAUDE_CODE_USE_BEDROCK=1` | 告诉 Claude Code 使用 AWS Bedrock 协议而非 Anthropic 原生协议 |
| `CLAUDE_CODE_SKIP_BEDROCK_AUTH=1` | 跳过标准 AWS SigV4 签名认证，由 Rakuten 网关用 Bearer Token 替代 |
| `CLAUDE_CODE_ENABLE_TELEMETRY=1` | 启用遥测数据上报 |
| `OTEL_METRICS_EXPORTER=otlp` | 将 metrics 通过 OTLP 协议上报 |
| `OTEL_LOGS_EXPORTER=otlp` | 将 logs 通过 OTLP 协议上报 |
| `OTEL_EXPORTER_OTLP_PROTOCOL` | 使用 HTTP + Protobuf 格式传输遥测数据 |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | 遥测数据上报到 Rakuten 的 OTEL 收集端点 |
| `OTEL_EXPORTER_OTLP_HEADERS` | 上报遥测数据时携带的认证 Header |

---

## 本质：企业代理模式

这是一个标准的**企业 AI 代理架构**：

- Rakuten 在 AWS Bedrock 上层封装了自己的网关
- 统一管理 API 访问控制、计费、审计和监控
- 员工使用公司分配的 `raik-pat-*` token，而不直接持有 Anthropic 或 AWS 的凭证
- 通过 OpenTelemetry（OTEL）标准将使用数据回传到公司内部可观测性平台
