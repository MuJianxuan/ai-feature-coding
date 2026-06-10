---
id: integration
version: 1
priority: 80
triggers: ["third-party", "webhook", "callback", "signature", "oauth", "integration", "第三方", "回调", "验签", "外部系统", "限流"]
required_sections: ["方案模板引用", "AC 覆盖映射", "API 契约", "数据模型", "前端设计", "后端设计", "性能考量", "风险和回滚"]
required_subsections: ["后端设计/外部系统边界", "后端设计/鉴权与签名", "后端设计/超时重试限流", "后端设计/降级策略", "风险和回滚/外部依赖风险"]
review_checklist: ["auth_signature", "timeout", "retry_rate_limit", "idempotent_callback", "fallback", "secret_handling", "sandbox_prod"]
---

# integration

## 适用场景

第三方 API、Webhook、外部系统同步、OAuth、支付/通知回调、签名验签。

## 输出要求

重点写清信任边界、失败策略、敏感信息处理。不要写真实 token、密钥、生产地址。

## 必填项

- 第三方系统边界。
- 鉴权方式。
- 请求签名/验签。
- 超时、重试、限流。
- 幂等和重复回调。
- 降级策略。
- 敏感信息处理。
- 沙箱/生产环境差异。

## 常见反模式

- 把第三方成功响应当成必然。
- Webhook 不验签。
- 回调重复投递导致重复入账/重复状态推进。
- 把 secret 值写进文档。

## 输出片段示例

```markdown
## 后端设计

### 外部系统边界
- 只依赖 Provider API 的订单查询和 Webhook 回调；Provider 不作为本系统事实源。

### 鉴权与签名
- API key 从环境变量读取；Webhook 使用 `X-Signature` HMAC-SHA256 验签。

### 超时重试限流
- 超时 3s；最多重试 2 次；429 按 `Retry-After` 退避。

### 降级策略
- Provider 不可用时标记为 pending_sync，由补偿任务重试。
```
