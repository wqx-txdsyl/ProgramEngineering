# C 同学实现说明：积分、兑换、测试（2026-09-25）

本文对应 [data-points-tasks.md](data-points-tasks.md) 的待办清单，说明已实现的范围、接口契约、共享文件改动点和测试结果。**merge 前请重点看第 3 节（共享文件改动清单）确认无冲突。**

## 1. 已实现范围

按文档要求的完成顺序：

| 优先级 | 内容 | 状态 |
| --- | --- | --- |
| 1 | 审核通过与发积分同一事务 | ✅ 已实现 |
| 2 | 积分余额与流水查询 | ✅ 已实现 |
| 2 | 奖励列表、兑换（幂等键）、兑换记录 | ✅ 已实现 |
| 扩展 | 取消未使用兑换单（退分 + 恢复库存） | ✅ 已实现，**契约需与 A/B 确认** |
| 待做 | 前端联调（A）、并发压测工具化、奖励管理后台 | 未开始（按文档"不做复杂商城"暂缓） |

业务规则（与文档 §2 对应）：

- 只有教师审核通过的成果产生积分，**固定 +10 分/条**（分值在 `app/services/points.py` 的 `REVIEW_APPROVED_POINTS`，团队确认后一处可改）；
- 一条成果最多奖励一次：靠 `point_transactions` 的唯一约束 `(user_id, source_type, source_id)`，source 键为 `("review_approved", submission.id)`；
- 积分按获益学生计入，不是按操作的教师；
- 已有的 approved 历史数据不自动补发；
- 时间统一存 UTC（ISO 8601 字符串），前端展示时自行转本地时区；
- 兑换记录状态机：`active → cancelled`（核销/已交付流程按文档暂缓，状态字段已预留）。

## 2. 新增接口契约

以实际 OpenAPI（`/openapi.json`）为准，以下为摘要。认证方式与现有接口相同（Bearer Token）。

| 方法与路径 | 权限 | 成功响应 | 说明 |
| --- | --- | --- | --- |
| `GET /api/points/me` | 学生 | 200 `{user_id, balance}` | 当前余额 |
| `GET /api/points/transactions?offset&limit` | 学生 | 200 流水数组，id 倒序 | 本人积分流水 |
| `GET /api/rewards?offset&limit` | 已登录 | 200 奖励数组 | 仅返回 `is_active=true` 的奖励 |
| `POST /api/rewards/{reward_id}/redeem` | 学生 | **201** 新建 / **200** 幂等重试 | 请求体 `{"request_key": "前端生成的唯一键"}`；同一键重试返回原单不重复扣费；同键换奖励 409 |
| `GET /api/rewards/redemptions/mine` | 学生 | 200 兑换单数组，id 倒序 | 本人兑换记录 |
| `POST /api/rewards/redemptions/{id}/cancel` | 学生 | 200 取消后的兑换单 | 仅本人、仅 `active` 可取消；退分 + 恢复库存 |

错误约定沿用现有风格：404 不存在 / 403 越权 / 409 状态或规则不允许（余额不足 `Insufficient balance`、库存不足 `Reward is out of stock`、重复处理等），响应体 `{"detail": "..."}`。

**给 A 的对接要点**：`request_key` 由前端生成并保存（提交兑换后若请求超时，用同一 key 重试是安全的）；兑换成功后刷新 `/api/points/me`；奖励列表不返回已下架条目。

## 3. 共享文件改动清单（merge 前重点核对）

遵循"只增不改"原则，对 B 的文件做了以下**最小新增**；`services/points.py`、`routers/points.py`、`routers/rewards.py`、`tests/` 四个 C 的预留空文件已填实现，不属于对 B 的改动。

| 文件 | 改动 |
| --- | --- |
| `app/models.py` | 导入行加 `CheckConstraint`、`datetime`；文件末尾新增 4 个类：`PointAccount`、`PointTransaction`、`Reward`、`Redemption`（未改动 Task/User/Submission） |
| `app/schemas.py` | 末尾新增 6 个契约类（Point/Reward/Redemption 相关），未改动原有类 |
| `app/main.py` | 新增 2 行 import + 2 行 `include_router`（points、rewards） |
| `app/services/learning.py` | `review_submission` 中在 `session.commit()` 前插入约 10 行：decision 为 approved 时调用 `award_review_points`，失败回滚后原样抛出；**其余逻辑一行未动** |
| `requirements.txt` | 追加 `pytest`、`httpx`（测试依赖） |
| 新增 `pytest.ini` | 配置 `pythonpath` 与 `testpaths`，从 `backend/` 目录直接运行 pytest |

## 4. 新增文件

| 文件 | 用途 |
| --- | --- |
| `app/services/points.py` | 发分、余额、流水、兑换、取消的全部业务逻辑 |
| `app/routers/points.py` | `/api/points/*` 接口 |
| `app/routers/rewards.py` | `/api/rewards/*` 接口 |
| `tests/conftest.py` | 隔离测试环境（内存库 + 覆盖 get_session + 账号工厂），不碰真实 `data/app.db` |
| `tests/test_auth.py` | 登录、错误密码、无效 Token、角色越权（7 个用例） |
| `tests/test_learning.py` | 提交查重、审核状态转换、退回重交、归属检查（7 个用例） |
| `tests/test_points.py` | 积分/兑换/事务一致性/并发/重启/升级（14 个用例） |
| `scripts/seed_rewards.py` | 幂等的奖励演示数据（可重复运行，已存在即跳过；无供应方的条目明确标注"演示"） |
| `scripts/check_data.py` | 对账：账户余额=流水和、兑换单与流水对应、库存非负、奖励来源真实存在 |

## 5. 测试结果与运行方法

```text
backend 目录下：
.venv\Scripts\python.exe -m pytest          → 28 passed（覆盖 docs §7 清单全部 13 项）
.venv\Scripts\python.exe -m scripts.seed_rewards
.venv\Scripts\python.exe -m scripts.check_data
```

§7 清单对照：登录/密码/Token/角色→test_auth；重复提交与他人成果→test_learning；审核恰好加一次分、发分失败回滚、退回重交不加分、不补发历史→test_points 前半；兑换一致性与三类失败不扣分→test_points 中段；幂等与同键换奖励、并发不超卖（双线程争最后库存）、重启落盘、升级不破坏旧数据→test_points 后半。

端到端冒烟（真实 uvicorn + data/app.db）：登录 → 发任务 → 提交 → 审核通过 → 余额 10 → 兑换 → 余额 0 → 幂等重试 → 取消 → 余额 10 → 对账通过，全部符合预期。

## 6. 数据库变更说明

- 新增 4 张表（`point_accounts`、`point_transactions`、`rewards`、`redemptions`），**未修改任何现有表**，因此 `create_all()` 直接兼容升级，无需迁移脚本；旧库升级行为已用测试锁定（`test_升级新增积分表不破坏原有数据`）。
- `point_accounts.balance` 有 `CHECK (balance >= 0)`；所有扣减走条件更新（`WHERE balance >= cost` / `WHERE stock > 0`）看影响行数，并发安全由数据库写锁 + 条件更新共同保证（并发测试验证）。
- 余额存于账户表、明细存于流水表，两者一致性由 `scripts/check_data.py` 对账兜底。

## 7. 需要团队确认的事项

1. 审核奖励 10 分/条的分值（现值只写在 `services/points.py` 一处）；
2. `POST /api/rewards/redemptions/{id}/cancel` 是文档拟议接口之外的补充，请 A/B 确认是否保留及前端是否展示"取消"入口；
3. 幂等键由前端生成的约定（长度 ≤100，建议 UUID）；
4. 演示奖励清单（`seed_rewards.py` 中的 4 条，均标注"演示"）；
5. requirements.txt 仍未锁版本（沿用现状），建议正式交付前统一 `pip freeze` 一次。
