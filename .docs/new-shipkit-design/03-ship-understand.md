# ship-understand 详细设计

## 目标
理解需求并产出结构化的 requirements.md，作为设计和实现的唯一需求源。

## 输入
- 需求描述（口头/文字）
- PRD 文档（.md/.docx/.pdf）
- 原型图（Figma/图片）
- 从 spec 加载：现有功能、业务域、命名规范

## 核心流程

```
接收输入 → 加载 spec → 解析需求 → grill-me 审查 → 生成 requirements.md
```

### Step 1: 加载 spec 上下文
```python
def load_spec_context(feature_dir):
    """从 spec 加载项目上下文"""
    spec_loader = SpecLoader(workspace_config)
    
    return {
        "existing_features": spec_loader.load_features(),
        "tech_stack": spec_loader.load_tech_stack(),
        "domain_glossary": spec_loader.load_domains(),
        "naming_conventions": spec_loader.load_conventions()
    }
```

### Step 2: 解析需求
根据输入类型：
- **口头描述**：多轮对话澄清（3-5 轮）
- **PRD 文档**：提取功能点、AC、约束
- **原型图**：解析页面流程、交互规则

### Step 3: grill-me 质询
在标记 `status: ready` 之前，启动 grill-me：

```python
def run_grill_me(requirements_draft):
    """审查需求清晰度"""
    questions = identify_blocking_issues(requirements_draft)
    
    for q in questions:
        # 每次只问一个
        answer = ask_user(
            question=q.text,
            recommended=q.recommended_answer,
            evidence=q.evidence_checked
        )
        update_requirements(answer)
    
    return "ready" if no_blocking_issues else "blocked"
```

grill-me 关注点：
- AC 是否可测试？
- 边界条件是否定义？
- 与现有功能的冲突？
- 非功能需求是否量化？

### Step 4: 生成 requirements.md

```markdown
---
status: ready
updated_at: "2026-06-09T12:00:00Z"
spec_refs: ["auth-flow", "user-domain"]
---

# 需求：用户登录

## 功能概述
用户可以使用邮箱+密码登录系统。

## Domain 模型
- D-AUTH-001: 用户认证流程
- D-USER-002: 用户会话管理

## 验收标准 (AC)

### AC-1: 正常登录
**Given** 用户已注册  
**When** 输入正确的邮箱和密码  
**Then** 跳转到首页并显示用户名

### AC-2: 密码错误
**Given** 用户已注册  
**When** 输入错误密码  
**Then** 显示"密码错误"，3 次后锁定账户

## 非功能需求
- 响应时间：< 500ms (P95)
- 并发：支持 1000 QPS
- 安全：密码加密存储（bcrypt）

## 约束
- 复用现有 User 表
- 兼容移动端
```

## 场景适配

### quick_start 模式
- 跳过 grill-me
- 只采集核心 AC
- 生成简化版 requirements.md

### full_flow 模式
- 完整 grill-me 审查
- 详细 Domain 建模
- 记录假设和风险

### prd_direct 模式
- 零提问
- 纯提取式生成
- 标注 PRD 章节引用

## 输出
- `requirements.md`（status: ready）
- 更新 `meta.yml.current_stage = design`
