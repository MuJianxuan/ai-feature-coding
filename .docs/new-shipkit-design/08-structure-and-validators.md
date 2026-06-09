# Feature 目录结构和 Validator 设计

## Feature 目录结构

```
.docs/feature-20260609-user-login/
├── meta.yml                    # 元数据（8 个核心字段）
├── requirements.md             # 需求文档
├── design.md                   # 技术设计（合并 API + 前后端）
├── build-plan.yml             # 构建任务清单
├── verification.md            # 验证报告
└── resource/                   # 原始资料
    ├── prd.md                 # 原始 PRD（如果有）
    ├── wireframes/            # 原型图（如果有）
    └── meeting-notes.md       # 会议纪要（如果有）
```

### meta.yml 完整示例

```yaml
feature_name: "用户登录"
current_stage: design  # understand | design | build | done
status: in_progress    # in_progress | blocked | completed
scenario: full_flow    # quick_start | full_flow | prd_direct | split_first

created_at: "2026-06-09T10:00:00Z"
updated_at: "2026-06-09T14:30:00Z"

# 引用的规范
spec_refs:
  - auth-flow
  - react-routing
  - rest-api-standard

# 产物文件索引
artifacts:
  requirements: requirements.md
  design: design.md
  build_plan: build-plan.yml
  verification: verification.md

# 只在阻塞时才写
blocked_reason: ""  # awaiting_grill_answers | awaiting_user_confirmation | test_failures

# 只在拆分场景下才写
parent_split_id: ""  # 如果来自 split，记录 parent id
split_dependency: []  # 依赖的其他 split feature
```

---

## Validator 设计

### 1. validate_requirements.py

**目标**：验证需求文档的质量和完整性

```python
#!/usr/bin/env python3
"""Requirements Validator - 验证需求文档质量"""

def validate_requirements(feature_dir):
    """验证 requirements.md"""
    req_file = f"{feature_dir}/requirements.md"
    
    checks = [
        check_frontmatter_exists(req_file),
        check_status_field(req_file),
        check_has_ac_section(req_file),
        check_ac_format(req_file),
        check_domain_model(req_file),
        check_nfr_quantified(req_file)
    ]
    
    errors = [c for c in checks if not c.passed]
    warnings = [c for c in checks if c.warning]
    
    return {
        "passed": len(errors) == 0,
        "errors": errors,
        "warnings": warnings
    }

def check_ac_format(req_file):
    """检查 AC 格式：必须包含 Given/When/Then"""
    content = read_file(req_file)
    ac_sections = extract_ac_sections(content)
    
    for ac in ac_sections:
        if not has_given_when_then(ac):
            return Check(
                name="AC 格式",
                passed=False,
                message=f"{ac.id} 缺少 Given/When/Then 结构"
            )
    
    return Check(name="AC 格式", passed=True)

def check_nfr_quantified(req_file):
    """检查非功能需求是否量化"""
    content = read_file(req_file)
    nfr_section = extract_nfr_section(content)
    
    if not nfr_section:
        return Check(
            name="非功能需求",
            passed=True,
            warning="未定义非功能需求（小功能可接受）"
        )
    
    # 检查是否有具体指标
    has_metrics = re.search(r'<\s*\d+\s*(ms|s|QPS|%)', nfr_section)
    if not has_metrics:
        return Check(
            name="非功能需求",
            passed=False,
            message="非功能需求缺少量化指标"
        )
    
    return Check(name="非功能需求", passed=True)
```

**验证规则**：
- ✅ frontmatter 存在且包含 status
- ✅ 至少有 1 个 AC
- ✅ AC 格式符合 Given/When/Then
- ✅ 有 Domain 模型定义
- ⚠️ 非功能需求量化（warning，不阻塞）

---

### 2. validate_design.py

**目标**：验证技术设计的完整性和一致性

```python
#!/usr/bin/env python3
"""Design Validator - 验证技术设计质量"""

def validate_design(feature_dir):
    """验证 design.md"""
    design_file = f"{feature_dir}/design.md"
    requirements_file = f"{feature_dir}/requirements.md"
    
    checks = [
        check_frontmatter_exists(design_file),
        check_api_contract_section(design_file),
        check_data_model_section(design_file),
        check_error_handling(design_file),
        check_ac_coverage(design_file, requirements_file),
        check_spec_compliance(design_file, feature_dir)
    ]
    
    errors = [c for c in checks if not c.passed]
    warnings = [c for c in checks if c.warning]
    
    return {
        "passed": len(errors) == 0,
        "errors": errors,
        "warnings": warnings
    }

def check_api_contract_section(design_file):
    """检查 API 契约章节完整性"""
    content = read_file(design_file)
    apis = extract_apis(content)
    
    for api in apis:
        if not has_request_response(api):
            return Check(
                name="API 契约",
                passed=False,
                message=f"{api.path} 缺少 Request/Response 定义"
            )
        
        if not has_error_responses(api):
            return Check(
                name="API 契约",
                passed=False,
                message=f"{api.path} 缺少错误响应定义"
            )
    
    return Check(name="API 契约", passed=True)

def check_ac_coverage(design_file, requirements_file):
    """检查设计是否覆盖所有 AC"""
    acs = extract_acs(requirements_file)
    design_content = read_file(design_file)
    
    uncovered = []
    for ac in acs:
        if ac.id not in design_content:
            uncovered.append(ac.id)
    
    if uncovered:
        return Check(
            name="AC 覆盖",
            passed=False,
            message=f"设计未覆盖 AC: {', '.join(uncovered)}"
        )
    
    return Check(name="AC 覆盖", passed=True)

def check_spec_compliance(design_file, feature_dir):
    """检查设计是否符合规范"""
    meta = load_meta(feature_dir)
    spec_refs = meta.get("spec_refs", [])
    
    if not spec_refs:
        return Check(
            name="规范遵循",
            passed=True,
            warning="未引用任何规范"
        )
    
    design_content = read_file(design_file)
    violations = []
    
    for spec_id in spec_refs:
        spec = load_spec(spec_id)
        if not check_compliance(design_content, spec):
            violations.append(spec_id)
    
    if violations:
        return Check(
            name="规范遵循",
            passed=False,
            message=f"违反规范: {', '.join(violations)}"
        )
    
    return Check(name="规范遵循", passed=True)
```

**验证规则**：
- ✅ API 契约包含 Request/Response/Error
- ✅ 数据模型定义存在
- ✅ 设计覆盖所有 AC
- ✅ 符合引用的 spec 规范
- ⚠️ 性能考量章节（warning）

---

### 3. validate_build.py

**目标**：验证构建产物的质量和 AC 覆盖

```python
#!/usr/bin/env python3
"""Build Validator - 验证构建产物质量"""

def validate_build(feature_dir):
    """验证 Build 阶段产物"""
    checks = [
        check_tests_exist(feature_dir),
        check_tests_passed(feature_dir),
        check_ac_test_coverage(feature_dir),
        check_code_quality(feature_dir),
        check_verification_report(feature_dir)
    ]
    
    errors = [c for c in checks if not c.passed]
    warnings = [c for c in checks if c.warning]
    
    return {
        "passed": len(errors) == 0,
        "errors": errors,
        "warnings": warnings
    }

def check_tests_passed(feature_dir):
    """检查测试是否通过"""
    test_results = run_tests(feature_dir)
    
    if test_results.failed > 0:
        return Check(
            name="测试通过",
            passed=False,
            message=f"{test_results.failed} 个测试失败"
        )
    
    return Check(name="测试通过", passed=True)

def check_ac_test_coverage(feature_dir):
    """检查 AC 测试覆盖"""
    requirements_file = f"{feature_dir}/requirements.md"
    verification_file = f"{feature_dir}/verification.md"
    
    acs = extract_acs(requirements_file)
    verification = read_file(verification_file)
    
    uncovered = []
    for ac in acs:
        if ac.id not in verification or "✅" not in verification:
            uncovered.append(ac.id)
    
    if uncovered:
        return Check(
            name="AC 测试覆盖",
            passed=False,
            message=f"未覆盖 AC: {', '.join(uncovered)}"
        )
    
    return Check(name="AC 测试覆盖", passed=True)

def check_code_quality(feature_dir):
    """检查代码质量"""
    # 运行 linter
    lint_result = run_linter(feature_dir)
    
    if lint_result.errors > 0:
        return Check(
            name="代码质量",
            passed=False,
            message=f"{lint_result.errors} 个 lint 错误"
        )
    
    if lint_result.warnings > 5:
        return Check(
            name="代码质量",
            passed=True,
            warning=f"{lint_result.warnings} 个 lint 警告"
        )
    
    return Check(name="代码质量", passed=True)
```

**验证规则**：
- ✅ 测试文件存在
- ✅ 所有测试通过
- ✅ 所有 AC 有对应测试
- ✅ 无 lint 错误
- ⚠️ Lint 警告 > 5（warning）
- ⚠️ 测试覆盖率 < 80%（warning）

---

## Validator 使用

```bash
# 验证需求
python validate_requirements.py .docs/feature-20260609-user-login

# 验证设计
python validate_design.py .docs/feature-20260609-user-login

# 验证构建
python validate_build.py .docs/feature-20260609-user-login

# 一键验证（当前阶段）
python validate_current_stage.py .docs/feature-20260609-user-login
```

输出示例：
```
✓ Requirements Validation Passed

Checks:
  ✅ frontmatter 存在
  ✅ AC 格式正确 (3 个 AC)
  ✅ Domain 模型定义
  ⚠️  非功能需求未量化（小功能可接受）

Summary: 3 passed, 0 errors, 1 warning
```
