# 关键机制补充设计

## 1. grill-me 精确触发规则

### 触发决策矩阵

| 场景 | 阶段 | 是否触发 | 条件 |
|------|------|----------|------|
| quick_start | Understand | **条件触发** | 发现歧义/冲突/缺失时强制触发 |
| quick_start | Design | **跳过** | - |
| full_flow | Understand | **必须** | 产出 status=ready 前触发 |
| full_flow | Design | **必须** | 产出 status=ready 前触发 |
| prd_direct | Understand | **跳过** | PRD 已完整 |
| prd_direct | Design | **条件触发** | 发现技术风险时触发 |

### 条件触发逻辑

```python
def should_trigger_grill_me(stage, scenario, draft_doc):
    """判断是否需要触发 grill-me"""
    
    if scenario == "prd_direct":
        return False  # PRD 直通默认跳过
    
    if scenario == "quick_start":
        # 快速模式：只在发现严重问题时触发
        issues = analyze_document(draft_doc)
        blocking_issues = [i for i in issues if i.severity == "blocking"]
        
        if blocking_issues:
            return True, blocking_issues
        return False, []
    
    if scenario == "full_flow":
        # 完整流程：必须触发
        return True, []
    
    return False, []

def analyze_document(doc):
    """分析文档质量，识别阻塞问题"""
    issues = []
    
    if stage == "understand":
        # 需求阶段检查
        if not has_clear_ac(doc):
            issues.append(Issue("缺少明确 AC", "blocking"))
        
        if has_conflicting_requirements(doc):
            issues.append(Issue("需求冲突", "blocking"))
        
        if references_undefined_features(doc):
            issues.append(Issue("引用未定义功能", "blocking"))
    
    elif stage == "design":
        # 设计阶段检查
        if has_performance_risks(doc):
            issues.append(Issue("性能风险", "warning"))
        
        if violates_spec(doc):
            issues.append(Issue("违反规范", "blocking"))
        
        if missing_error_handling(doc):
            issues.append(Issue("缺少错误处理", "blocking"))
    
    return issues
```

### 质询流程

```python
def run_grill_me(stage, draft_doc, feature_dir):
    """执行 grill-me 质询"""
    
    # 1. 识别问题
    all_questions = identify_all_questions(draft_doc, feature_dir)
    
    # 2. 过滤阻塞问题
    blocking = [q for q in all_questions if q.is_blocking]
    
    # 3. 逐个质询（每次只问一个）
    for q in blocking:
        # 先检查是否能从仓库/spec 找到答案
        answer = try_find_answer_in_repo(q, feature_dir)
        
        if answer:
            # 自动解决
            update_document(draft_doc, q, answer)
            log_decision(f"自动解决: {q.id} - {answer.summary}")
        else:
            # 需要用户决策
            user_answer = ask_user(
                question=q.text,
                recommended=q.recommended_answer,
                evidence=q.evidence_checked,
                impact=q.impact
            )
            update_document(draft_doc, q, user_answer)
    
    # 4. 检查是否还有阻塞
    if no_more_blocking_issues(draft_doc):
        mark_as_ready(draft_doc)
        return "ready"
    else:
        mark_as_blocked(feature_dir, "awaiting_grill_answers")
        return "blocked"
```

---

## 2. Split 依赖检查机制

### 依赖追踪数据结构

```yaml
# splits.yml
parent_requirement: "用户管理系统"
splits:
  - id: REQ-001
    name: 用户注册
    feature_dir: feature-20260609-user-register
    status: completed
    completed_at: "2026-06-09T16:00:00Z"
    
  - id: REQ-002
    name: 用户登录
    feature_dir: feature-20260609-user-login
    status: in_progress
    dependencies: [REQ-001]
    blocked_by: []  # 空表示无阻塞
    
  - id: REQ-003
    name: 权限管理
    feature_dir: feature-20260609-rbac
    status: pending
    dependencies: [REQ-002]
    blocked_by: [REQ-002]  # REQ-002 未完成
```

### 依赖检查逻辑

```python
def check_split_dependencies(splits_file):
    """检查拆分需求的依赖状态"""
    splits_data = load_yaml(splits_file)
    splits = splits_data["splits"]
    
    # 构建依赖图
    dep_graph = build_dependency_graph(splits)
    
    # 更新阻塞状态
    for split in splits:
        if split["status"] == "completed":
            continue
        
        blocked_by = []
        for dep_id in split.get("dependencies", []):
            dep_split = find_split_by_id(splits, dep_id)
            if dep_split["status"] != "completed":
                blocked_by.append(dep_id)
        
        split["blocked_by"] = blocked_by
        
        # 更新 feature meta.yml
        if split.get("feature_dir"):
            update_feature_meta(
                split["feature_dir"],
                blocked=(len(blocked_by) > 0),
                blocked_reason=f"等待依赖: {', '.join(blocked_by)}"
            )
    
    save_yaml(splits_file, splits_data)
    return splits

def can_start_split(split_id, splits_file):
    """判断拆分需求是否可以开始"""
    splits = load_yaml(splits_file)["splits"]
    split = find_split_by_id(splits, split_id)
    
    if not split:
        return False, "Split ID 不存在"
    
    if split["status"] == "completed":
        return False, "已完成"
    
    if len(split.get("blocked_by", [])) > 0:
        return False, f"依赖未完成: {split['blocked_by']}"
    
    return True, "可以开始"
```

### Orchestrator 集成

```python
def handle_continue_split_feature(split_id, splits_file):
    """继续拆分出的 feature"""
    
    # 1. 检查依赖
    can_start, reason = can_start_split(split_id, splits_file)
    
    if not can_start:
        return f"❌ 无法开始：{reason}"
    
    # 2. 获取 feature_dir
    splits = load_yaml(splits_file)["splits"]
    split = find_split_by_id(splits, split_id)
    feature_dir = split["feature_dir"]
    
    # 3. 正常流程
    return continue_feature(feature_dir)

def on_feature_completed(feature_dir):
    """Feature 完成时回调"""
    
    # 检查是否属于 split
    meta = load_meta(feature_dir)
    if not meta.get("parent_split_id"):
        return
    
    # 更新 splits.yml
    splits_file = find_splits_file(meta["parent_split_id"])
    update_split_status(
        splits_file,
        split_id=meta["split_id"],
        status="completed"
    )
    
    # 检查并解除下游阻塞
    check_split_dependencies(splits_file)
    
    # 通知用户
    notify_next_available_splits(splits_file)
```

---

## 3. Build 任务生成算法

### 任务提取规则

```python
def generate_build_tasks(design_file, requirements_file):
    """从设计文档生成构建任务"""
    
    design = parse_design(design_file)
    requirements = parse_requirements(requirements_file)
    
    tasks = []
    task_id = 1
    
    # 1. 数据层任务（优先级最高）
    if design.has_data_model_changes():
        for table in design.data_model.new_tables:
            tasks.append({
                "id": f"T-{task_id:03d}",
                "name": f"创建 {table.name} 表",
                "type": "migration",
                "priority": "high",
                "files": [f"migrations/{task_id:03d}_create_{table.name}.sql"],
                "ac_refs": extract_ac_refs(table, requirements),
                "dependencies": [],
                "estimated_minutes": 10
            })
            task_id += 1
        
        for table in design.data_model.modified_tables:
            tasks.append({
                "id": f"T-{task_id:03d}",
                "name": f"修改 {table.name} 表",
                "type": "migration",
                "priority": "high",
                "files": [f"migrations/{task_id:03d}_alter_{table.name}.sql"],
                "dependencies": find_table_dependencies(table, tasks),
                "estimated_minutes": 15
            })
            task_id += 1
    
    migration_task_ids = [t["id"] for t in tasks]
    
    # 2. 后端任务
    if design.has_backend_changes():
        # Service 层
        for service in design.backend.services:
            tasks.append({
                "id": f"T-{task_id:03d}",
                "name": f"实现 {service.name}",
                "type": "backend",
                "priority": "high",
                "files": [service.file_path],
                "dependencies": migration_task_ids,  # 依赖所有数据层任务
                "ac_refs": service.ac_refs,
                "estimated_minutes": estimate_service_complexity(service)
            })
            service_task_id = f"T-{task_id:03d}"
            task_id += 1
        
        # Controller/Route 层
        for api in design.api_contract.apis:
            tasks.append({
                "id": f"T-{task_id:03d}",
                "name": f"实现 API {api.method} {api.path}",
                "type": "backend",
                "priority": "medium",
                "files": [api.controller_file],
                "dependencies": [service_task_id],
                "ac_refs": api.ac_refs,
                "estimated_minutes": 20
            })
            task_id += 1
    
    backend_task_ids = [t["id"] for t in tasks if t["type"] == "backend"]
    
    # 3. 前端任务（可与后端部分并行）
    if design.has_frontend_changes():
        # 状态管理
        if design.frontend.state_management:
            tasks.append({
                "id": f"T-{task_id:03d}",
                "name": "实现状态管理",
                "type": "frontend",
                "priority": "high",
                "files": design.frontend.state_files,
                "dependencies": [],  # 可独立开始
                "estimated_minutes": 30
            })
            state_task_id = f"T-{task_id:03d}"
            task_id += 1
        
        # 页面组件（依赖后端 API）
        for page in design.frontend.pages:
            tasks.append({
                "id": f"T-{task_id:03d}",
                "name": f"实现页面 {page.path}",
                "type": "frontend",
                "priority": "medium",
                "files": page.component_files,
                "dependencies": backend_task_ids + [state_task_id],
                "ac_refs": page.ac_refs,
                "estimated_minutes": estimate_page_complexity(page)
            })
            task_id += 1
    
    # 4. 集成任务（最后）
    tasks.append({
        "id": f"T-{task_id:03d}",
        "name": "集成测试和端到端验证",
        "type": "integration",
        "priority": "high",
        "files": ["tests/integration/", "tests/e2e/"],
        "dependencies": [t["id"] for t in tasks],  # 依赖所有任务
        "ac_refs": [ac.id for ac in requirements.acs],
        "estimated_minutes": 60
    })
    
    return tasks

def estimate_service_complexity(service):
    """估算 Service 复杂度"""
    base = 30
    if service.has_external_api_calls:
        base += 20
    if service.has_complex_business_logic:
        base += 30
    if service.has_transaction_handling:
        base += 15
    return base

def estimate_page_complexity(page):
    """估算页面复杂度"""
    base = 20
    base += len(page.forms) * 15
    base += len(page.tables) * 10
    base += len(page.charts) * 20
    if page.has_real_time_updates:
        base += 25
    return base
```

### 任务粒度控制

**原则**：
- 单个任务 ≤ 60 分钟
- 每个任务关联明确的 AC
- 依赖关系清晰可追踪
- 支持增量验证（每完成一个任务就测试）

---

## 4. spec 沉淀标准和多项目隔离

### 沉淀标准

```python
def should_propose_new_spec(feature_dir):
    """判断是否应该沉淀新规范"""
    
    criteria = {
        "复用次数": check_reuse_count(feature_dir),
        "模式稳定性": check_pattern_stability(feature_dir),
        "影响范围": check_impact_scope(feature_dir),
        "复杂度": check_pattern_complexity(feature_dir)
    }
    
    # 评分规则
    score = 0
    
    if criteria["复用次数"] >= 3:
        score += 40  # 已在 3 个 feature 中使用
    
    if criteria["模式稳定性"] == "stable":
        score += 30  # 模式无频繁变更
    
    if criteria["影响范围"] == "cross_module":
        score += 20  # 跨模块使用
    
    if criteria["复杂度"] == "medium_to_high":
        score += 10  # 有一定复杂度，值得文档化
    
    # 60 分及格线
    if score >= 60:
        return True, generate_spec_proposal(feature_dir, criteria)
    
    return False, None

def generate_spec_proposal(feature_dir, criteria):
    """生成规范提案"""
    return {
        "proposed_spec_id": suggest_spec_id(feature_dir),
        "category": suggest_category(criteria["影响范围"]),
        "title": "...",
        "content": extract_pattern(feature_dir),
        "applies_to": extract_applicable_paths(feature_dir),
        "justification": criteria
    }
```

### 多项目 spec 加载隔离

```python
class SpecLoader:
    def load_for_feature(self, feature_dir):
        """为 feature 加载适用的规范"""
        
        workspace_config = find_workspace_config(feature_dir)
        meta = load_meta(feature_dir)
        
        if workspace_config.mode == "single_project":
            # 单项目：加载所有规范
            return self._load_all_specs(workspace_config.spec_root)
        
        elif workspace_config.mode == "project_group":
            # 多项目：按项目隔离 + shared
            target_projects = meta.get("projects", [])
            
            specs = {}
            
            # 1. 加载 shared 规范（所有项目可用）
            shared_specs = self._load_specs(
                f"{workspace_config.spec_root}/_shared"
            )
            specs.update(shared_specs)
            
            # 2. 加载项目专属规范
            for project in target_projects:
                project_specs = self._load_specs(
                    f"{workspace_config.spec_root}/{project}",
                    scope=f"project:{project}"
                )
                specs.update(project_specs)
            
            return specs
    
    def _load_specs(self, spec_dir, scope="shared"):
        """加载指定目录的规范"""
        index_file = f"{spec_dir}/INDEX.md"
        if not exists(index_file):
            return {}
        
        index = parse_index(index_file)
        specs = {}
        
        for entry in index:
            spec_content = read_file(f"{spec_dir}/{entry.file_path}")
            spec = parse_spec(spec_content)
            spec["_scope"] = scope  # 标记来源
            specs[entry.spec_id] = spec
        
        return specs
```

### 规范优先级

当 shared 和 project 有同名规范时：
- **project 规范优先**（更具体）
- shared 规范作为 fallback
- 记录 warning 提示用户

---

## 性能和安全（简要）

### 性能优化
- Spec 索引缓存（读取一次，内存保持）
- Feature 列表惰性加载（只扫描 meta.yml）
- Validator 并行执行
- 大文件流式处理

### 安全考量
- Feature 目录不包含敏感信息（密码、token）
- Spec 修改记录 git commit author
- 生产部署信息不入 feature 文档
- 可选：feature 目录加密（企业版）
