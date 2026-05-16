---
doc_type: guide
topic: error-handling
scope: coding
status: active
tags: [reliability]
related: [logging]
updated_at: 2026-05-16T10:30:00+08:00
---

# 错误处理 思考清单

## 写代码前先想

- [ ] 这个错误是用户可恢复（如输入校验失败）还是系统级（如数据库不可达）？两类的处理路径完全不同。
- [ ] 错误是否应该向上抛出？还是在当前层就近吞掉并降级？
- [ ] 是否需要打点告警（PagerDuty / Sentry）？哪个等级？
- [ ] 是否需要重试？如果重试，是否幂等？退避策略是什么？
- [ ] 用户最终能看到什么样的错误信息？是否暴露了不该暴露的内部细节？
- [ ] 这个错误路径是否在测试中有覆盖？
- [ ] 是否会污染上游事务（数据库 / 消息队列）状态？

## 写完后核对

- [ ] 所有 `catch` 是否都打了 log（含 stack trace、上下文 id）？
- [ ] 是否吞了不该吞的异常（空 `except: pass` 或 `catch (Exception e) {}`）？
- [ ] 给用户的错误响应是否符合 API 错误格式约定？
- [ ] 关键失败路径是否有对应单元测试或集成测试？
- [ ] 是否有 finally / defer 清理资源（连接、文件、锁）？

## 相关 spec

- [[logging]]
