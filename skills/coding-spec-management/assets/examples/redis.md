---
doc_type: spec
topic: redis
scope: coding
status: active
tags: [cache, infra]
related: []
updated_at: 2026-05-16T10:30:00+08:00
---

# Redis 使用规范

## 原则

- key 必带业务前缀 — Why: 多业务共享集群时避免命名冲突导致误删或互踩。
- 缓存只是加速层，不是事实源 — Why: 缓存失效或被清空时业务必须仍能从主存正常工作。
- 任何写入必须显式 TTL — Why: 永不过期的 key 是内存泄漏的主要来源。
- 大 key 与热 key 提前评估 — Why: 单 key 过大或过热会拖垮整个集群分片。

## 规约

- **MUST** key 命名格式 `<biz>:<entity>:<id>`，全小写，分隔符用冒号。
  ```
  // DO
  user:profile:1001
  // DON'T
  UserProfile_1001
  ```

- **MUST** 所有 `SET` 调用必须显式传 TTL；禁止使用无过期时间的 `SET`。
  ```
  // DO
  redis.set("user:profile:1001", json, ex=3600)
  // DON'T
  redis.set("user:profile:1001", json)
  ```

- **MUST NOT** 在 Redis 中存放未脱敏的用户敏感数据（手机号、身份证、密码哈希）。

- **MUST NOT** 使用 `KEYS *` 或无 `MATCH` 限制的 `SCAN` 在生产环境扫描 key。

- **SHOULD** 单 key value 大小控制在 10KB 以内；超过 100KB 必须拆分或改用对象存储。

- **SHOULD** 高频读写的 key 使用本地缓存 + Redis 二级结构，避免单 key 热点。

- **SHOULD** 分布式锁优先使用 Redlock 或 `SET key value NX PX <ttl>`，禁止用 `SETNX` + 单独 `EXPIRE`（非原子）。

- **MAY** 对低频但体积大的对象使用压缩（如 zstd）后再存入。

## 示例

```python
# DO: 连接池 + 显式 TTL + 业务前缀
import json
import redis

pool = redis.ConnectionPool(host="redis", port=6379, max_connections=50, decode_responses=True)
r = redis.Redis(connection_pool=pool)

def cache_user_profile(user_id: int, profile: dict, ttl: int = 3600) -> None:
    key = f"user:profile:{user_id}"
    r.set(key, json.dumps(profile), ex=ttl)
```

```python
# DON'T: 每次新建连接、key 无前缀、无 TTL
r = redis.Redis(host="redis")
r.set(str(user_id), json.dumps(profile))
```
