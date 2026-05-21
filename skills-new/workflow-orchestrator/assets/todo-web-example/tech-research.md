---
doc_type: tech_research
doc_status: ready
updated_at: 2026-05-21T00:00:00+08:00
---

# Tech Research

## 1. 技术问题清单

| ID | 问题 | 为什么要查 |
| --- | --- | --- |
| TR-01 | 前端脚手架选择 | 需要快速初始化可测试的单页应用 |
| TR-02 | 后端框架选择 | 需要低门槛承载 CRUD API |
| TR-03 | 持久化方式选择 | 需要验证真实存储而不是纯内存状态 |

## 2. 外部证据

| ID | 来源类型 | 来源 | 版本 / 日期 | 结论 | 适用范围 |
| --- | --- | --- | --- | --- | --- |
| E-01 | official docs | Vite docs | 2026-05-21 | 适合作为前端官方脚手架 | greenfield frontend |
| E-02 | official docs | Express docs | 2026-05-21 | 适合作为轻量 REST backend | greenfield backend |
| E-03 | official docs | SQLite docs | 2026-05-21 | 足以支撑样例级 CRUD 持久化 | local persistence |

## 3. 脚手架 / 基础设施候选

| 候选 | 来源 | 优点 | 风险 | 结论 |
| --- | --- | --- | --- | --- |
| Vite | official | 快速、现代、官方生态好 | 需要补前端测试配置 | 采用 |
| Express | official | 轻量、CRUD 足够 | 需手动组织目录 | 采用 |
| SQLite | official | 简单、可持久化、便于验证 | 并发能力一般 | 样例采用 |

