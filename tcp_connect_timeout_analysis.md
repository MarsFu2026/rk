# 技术分析：如何从报错信息判断是 TCP 握手阶段超时

## 结论

错误发生在 **TCP 连接建立阶段**，而不是认证失败或服务器拒绝请求。

---

## 调用栈分析

报错的调用栈从底层到顶层：

```
httpcore/_backends/sync.py   connect_tcp         ← 第1层：尝试建立 TCP 连接
httpcore/_sync/connection.py   _connect          ← 第2层：连接过程
httpcore/_sync/connection.py   handle_request    ← 第3层：处理请求
httpcore/_sync/connection_pool.py                ← 连接池调度
httpx/_transports/default.py                     ← HTTP 传输层
anthropic/_base_client.py                        ← SDK 层
```

栈底（最底层）停在 `connect_tcp`，说明程序**还没有发出任何 HTTP 数据**就已经超时退出。

---

## 关键证据：异常类型

最底层抛出的异常是：

```
httpcore.ConnectTimeout: timed out
```

httpcore 针对不同网络阶段定义了不同的异常类型：

| 异常类 | 触发时机 | 含义 |
|--------|----------|------|
| `ConnectTimeout` | `connect()` 系统调用超时 | **TCP 三次握手未完成** |
| `ReadTimeout` | TCP 已连接，等待响应超时 | 服务器处理慢或无响应 |
| `WriteTimeout` | TCP 已连接，发送请求超时 | 本地发送缓慢 |
| `ConnectError` | `connect()` 返回错误 | TCP 被主动拒绝（RST） |

`ConnectTimeout` 明确说明：**SYN 包发出后，没有收到服务器的 SYN-ACK 回应，等到超时。**

---

## 与其他错误场景的对比

### 如果是认证失败（401 / 403）

TCP 连接会先建立成功，服务器返回 HTTP 错误码，SDK 会抛出：

```
anthropic.AuthenticationError: 401 Unauthorized
```

调用栈会停在 HTTP 响应解析层，而不是 `connect_tcp`。

### 如果是服务器内部错误（500）

同样需要 TCP 连接成功，才会有 HTTP 响应，抛出：

```
anthropic.APIStatusError: 500 Internal Server Error
```

### 本次错误

TCP 握手阶段就超时，**连 HTTP 请求都没发出去**，说明：

- 网络包被丢弃（防火墙 / IP 白名单）
- 或服务器根本不响应该 IP 的连接请求
