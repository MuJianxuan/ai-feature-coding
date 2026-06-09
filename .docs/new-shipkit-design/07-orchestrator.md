# ship-orchestrator 简化版设计

## 目标
统一入口，自动识别场景和路由到正确阶段。

## 核心原则
- **宽松触发**：用户只需表达开发意图
- **智能路由**：自动判断从哪个阶段开始
- **透明状态**：随时告知当前进度和下一步

## 触发模式

### 1. 新建 feature
```bash
用户："做一个用户登录功能"
```

Orchestrator 判断：
- 没有附件 → 口头描述
- 没有引用已有代码 → 新功能
- 场景：full_flow
- 起点：ship-understand

### 2. 提供 PRD
```bash
用户："启动新需求，PRD 在 resource/login-prd.md"
```

Orchestrator 判断：
- 有完整 PRD 文档
- 场景：prd_direct
- 起点：ship-understand（prd 解析模式）

### 3. 恢复开发
```bash
用户："继续上次的登录功能"
```

Orchestrator 判断：
- 读取 meta.yml.current_stage
- 检查阻塞状态
- 恢复到 current_stage

### 4. 需求拆分
```bash
用户："这个需求太大了，帮我拆分一下：<大需求描述>"
```

Orchestrator 判断：
- 显式拆分请求
- 场景：split_first
- 起点：ship-split

## 路由决策树

```
用户输入
    │
    ▼
┌─────────────┐
│ 是恢复模式？ │
└──┬────────┬─┘
   Y        N
   │        │
   ▼        ▼
读取meta  ┌─────────────┐
继续推进  │ 是拆分请求？ │
          └──┬────────┬─┘
             Y        N
             │        │
             ▼        ▼
       ship-split  ┌─────────────┐
                   │ 有完整PRD？  │
                   └──┬────────┬─┘
                      Y        N
                      │        │
                      ▼        ▼
               prd_direct   full_flow
               ship-understand
```

## 状态推进规则

```python
def can_advance_to_next_stage(feature_dir):
    """判断是否可以推进到下一阶段"""
    meta = load_meta(feature_dir)
    current = meta.current_stage
    
    rules = {
        "understand": {
            "next": "design",
            "requires": [
                ("requirements.md", "status", "ready"),
                ("meta.yml", "status", "in_progress")
            ]
        },
        "design": {
            "next": "build",
            "requires": [
                ("design.md", "status", "ready"),
                ("user_confirmation", "design_approved", True)
            ]
        },
        "build": {
            "next": "done",
            "requires": [
                ("verification.md", "all_ac_passed", True),
                ("tests", "status", "passed")
            ]
        }
    }
    
    rule = rules.get(current)
    if not rule:
        return False
    
    for file, field, expected in rule["requires"]:
        actual = get_field(feature_dir, file, field)
        if actual != expected:
            return False, f"等待 {file}.{field} = {expected}"
    
    return True, rule["next"]
```

## 阻塞处理

### 阻塞类型
1. **缺少输入**：需求描述不清晰
2. **grill-me 发现问题**：有 blocking 问题未解决
3. **测试失败**：Build 阶段测试不通过
4. **用户未确认**：Design → Build 等待确认

### 阻塞恢复
```python
def handle_blocked_feature(feature_dir):
    """处理阻塞的 feature"""
    meta = load_meta(feature_dir)
    
    if meta.status != "blocked":
        return
    
    # 分析阻塞原因
    reason = meta.blocked_reason
    
    if reason == "awaiting_grill_answers":
        # 重新运行 grill-me
        pending_questions = load_pending_questions(feature_dir)
        for q in pending_questions:
            answer = ask_user(q)
            save_answer(answer)
        
        # 解除阻塞
        meta.status = "in_progress"
        meta.blocked_reason = ""
        save_meta(meta)
    
    elif reason == "awaiting_user_confirmation":
        # 提示用户确认
        prompt_user_confirmation(meta.current_stage)
    
    elif reason == "test_failures":
        # 显示失败的测试
        show_failed_tests(feature_dir)
        # 提供修复建议
        suggest_fixes(feature_dir)
```

## 输出格式

### 新建时
```
✓ 场景识别：完整流程（口头需求 → 设计 → 实现）
✓ 起点：理解需求阶段

当前阶段：Understand（理解需求）
目标：产出结构化的 requirements.md

下一步：
我会通过 3-5 轮对话了解需求细节，然后进行质量审查。
准备好了吗？
```

### 恢复时
```
✓ 加载 feature：用户登录
✓ 当前阶段：Design（技术设计）
✓ 状态：等待确认

已完成：
✅ requirements.md (5 个 AC)

当前产物：
📄 design.md (status: ready)
  - 2 个 API 接口
  - 2 张数据表
  - 3 个前端页面

下一步：
设计方案已完成，是否开始实现？
[yes] 开始 Build 阶段
[modify] 修改设计方案
[review] 查看详细设计
```

## 简化点总结

与旧方案对比：
- ❌ 删除 14 个细阶段 → ✅ 4 个主阶段
- ❌ 删除 3 道硬门禁 + 签字 → ✅ 1 道用户确认
- ❌ 删除复杂状态同步 → ✅ meta.yml 单一事实源
- ❌ 删除 27 个 validator → ✅ 3 个核心 validator
- ❌ 删除 Source Code Edit Barrier → ✅ 到 Build 阶段即可编辑
