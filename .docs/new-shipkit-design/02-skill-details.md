# 技能详细设计 v1

## 1. ship-split（需求拆分）

### 目标
将大需求拆分成多个独立的、可单独交付的小需求。

### 输入
- 大需求描述（文本）
- TAPD/Jira 链接或导出数据
- 会议纪要、用户故事
- 现有项目上下文（从 spec 加载）

### 处理流程
1. 分析需求规模和复杂度
2. 识别独立的功能模块
3. 检查依赖关系
4. 生成拆分建议
5. 用户确认拆分方案
6. （可选）自动创建 TAPD/Jira 任务

### 输出
```yaml
# splits.yml
parent_requirement: "用户管理系统"
split_strategy: "by_user_story"
splits:
  - id: "REQ-001"
    name: "用户注册"
    priority: high
    estimated_days: 2
    dependencies: []
    tapd_id: "1234567"  # 如果创建了
    
  - id: "REQ-002"
    name: "用户登录"
    priority: high
    estimated_days: 1
    dependencies: ["REQ-001"]
    tapd_id: "1234568"
```

### 拆分原则
- 每个子需求可独立测试和交付
- 单个子需求工作量 ≤ 3 天
- 明确标注依赖关系
- 优先级清晰

### TAPD 集成
```python
# tapd_client.py
def create_story(workspace_id, title, description, priority):
    """创建 TAPD 用户故事"""
    pass

def update_story(story_id, fields):
    """更新故事状态"""
    pass
```

### 何时使用
- 用户说"这个需求很大，帮我拆分一下"
- 需求描述超过 5 个独立功能点
- 需要生成 TAPD 任务清单

### 何时不用
- 需求已经很小（<= 3 天）
- 用户明确只做其中一部分
