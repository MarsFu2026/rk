# 方案选择：单仓库 vs 多仓库

## 背景

当前 `rk` 仓库已包含 Design Doc Review Agent 的 CI 工具代码。在此基础上新增业务代码时，有两种组织方式可选。

---

## 方案 A：在同一 repo 扩展

**适用场景**：新增代码与当前 Agent 功能直接相关（如 Web 界面、扩展 Agent 能力）

```
rk/
├── .github/workflows/       # CI 配置
├── agent/                   # 现有 Agent 代码
├── src/                     # 新增：正式业务代码
├── tests/                   # 新增：测试
└── requirements.txt
```

**优点**：
- CI workflow 可直接对业务代码跑测试、lint、部署，天然集成
- 无需跨仓库授权配置

**缺点**：
- 功能不相关时，仓库职责不清晰
- 不同团队协作时权限难以细分

---

## 方案 B：独立业务 repo，单独配置 CI

**适用场景**：新代码与 Design Doc Review Agent 无直接关联，属于独立项目

```
rk/（CI 工具仓库）                    business-app/（业务仓库）
├── .github/workflows/               ├── src/
│   └── design-doc-review.yml        ├── tests/
├── agent/                           └── .github/workflows/
│   └── review.py                        └── ci.yml
└── ...
```

**优点**：
- 职责清晰，`rk` 专注 CI 工具维护
- 业务仓库可独立迭代，互不干扰
- 适合多项目、多团队场景

**缺点**：
- 需要额外的跨仓库授权配置

---

## 决策建议

| 情况 | 推荐方案 |
|---|---|
| 新代码是对当前 Agent 的功能扩展 | 方案 A |
| 新代码是与 Agent 无关的独立项目 | 方案 B |
| 预期有多个项目需要接入 CI | 方案 B |

> 方案 B 的具体实现见 [方案B_多仓库CI架构.md](./方案B_多仓库CI架构.md)
