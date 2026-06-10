---
name: ship-understand
description: "新 ShipKit Understand 阶段。加载 spec，解析需求/PRD/原型，必要时调用 grill-me，产出 requirements.md(status: ready)。"
---

# ship-understand

## 目标

把用户输入变成可设计、可验证的 `requirements.md`。它是后续设计和实现的唯一需求源。

## 输入

- 口头/文字需求。
- PRD、原型、图片、会议纪要。
- `meta.yml.scenario`。
- `ship-spec` 加载的 existing-features、domain glossary、naming conventions。

## 流程

1. 读取或创建 feature 目录和 `meta.yml`。
2. 调用 `ship-spec` 加载 Understand 阶段上下文。
3. 按输入类型解析需求：
   - 口头描述：澄清核心目标、用户、边界、AC。
   - PRD：提取功能点、AC、约束，并保留章节引用。
   - 原型：提取页面流程、状态、交互规则。
4. 生成 `requirements.md` 草稿。
5. 按场景决定是否调用 `ship-grill-me`。
6. 通过 `validate_requirements.py`。
7. 标记 `requirements.md status: ready`，更新 `meta.yml.current_stage: design`。

## grill-me 触发

| 场景 | Understand 触发策略 |
|---|---|
| `quick_start` | 只有发现 blocking 问题才触发 |
| `full_flow` | 必须触发 |
| `prd_direct` | 默认跳过；只做提取，不扩写需求 |
| `split_first` | 子 feature 按 `full_flow` 处理 |

blocking 问题包括：没有可测试 AC、需求互相冲突、引用未定义功能、边界条件缺失且会影响实现。

## requirements.md 结构

```markdown
---
status: ready
updated_at: "2026-06-09T12:00:00Z"
spec_refs: ["auth-flow", "user-domain"]
---

# 需求：用户登录

## 功能概述
一句话说明用户价值和功能边界。

## Domain 模型
- D-AUTH-001: 用户认证流程

## 验收标准 (AC)

### AC-1: 正常登录
**Given** 用户已注册  
**When** 输入正确的邮箱和密码  
**Then** 跳转到首页并显示用户名

## 非功能需求
- 响应时间：P95 < 500ms
- 并发：支持 1000 QPS

## 约束
- 复用现有 User 表
- 兼容移动端

## 假设和风险
- 假设现有邮箱服务可复用。
```

## 质量标准

必须满足：

- frontmatter 有 `status` 和 `updated_at`。
- 至少 1 个 AC。
- 每个 AC 使用 Given/When/Then。
- 有 Domain 模型或明确说明不涉及业务域。
- 非功能需求若存在，尽量量化；小功能可缺省但要接受 warning。
- 与现有功能冲突必须解决或写入风险。

## 状态更新

成功后：

```yaml
current_stage: design
status: in_progress
artifacts:
  requirements: requirements.md
```

失败或等待回答：

```yaml
current_stage: understand
status: blocked
blocked_reason: awaiting_grill_answers
```

## 不做什么

- 不做技术方案细节；那是 `ship-design`。
- 不写业务代码。
- 不为了填模板编造需求；无法确定就质询。
