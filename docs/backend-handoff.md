# B 同学交接：已完成后端与接口调用清单

核对日期：2026-09-25。本文依据当前源代码及应用生成的 OpenAPI 编写。

## 1. 已完成内容

| 模块 | 已完成能力 | 主要文件 |
| --- | --- | --- |
| 应用与配置 | 应用启动、路由注册、读取密钥和数据库路径 | `backend/app/main.py`、`config.py` |
| 数据存储 | SQLite 连接、建表、每次请求使用数据库会话 | `backend/app/database.py`、`models.py` |
| 登录与权限 | 密码哈希、JWT 登录、获取身份、教师/学生权限检查 | `routers/auth.py`、`services/auth.py`、`dependencies.py` |
| 任务 | 教师创建；登录用户查看列表和详情 | `routers/tasks.py` |
| 学生成果 | 创建提交、只看自己的记录、修改被退回的成果 | `routers/submissions.py` |
| 教师审核 | 查询待审核记录、通过或退回、填写反馈 | `routers/reviews.py`、`services/learning.py` |
| 输入输出规范 | 字段长度、必填项、状态枚举、禁止额外输入字段 | `schemas.py` |
| 测试账号 | 交互式创建 teacher/student，已有账号跳过 | `scripts/seed.py` |

数据库有 `tasks`、`users`、`submissions` 三张业务表。成果表的 `(task_id, student_id)` 具有联合唯一约束，一名学生针对同一个任务只有一条记录，重交修改原记录。

尚未实现：积分、兑换、前端、跨域配置、班级隔离、用户注册、文件上传、完整审核历史、服务端注销、版本化数据库迁移。

## 2. 调用约定

- 本机后端地址：`http://127.0.0.1:8000`。
- 请求和响应使用 JSON；带请求体时设置 `Content-Type: application/json`。
- 登录之外的业务接口需携带请求头 `Authorization: Bearer TOKEN_VALUE`，将 `TOKEN_VALUE` 替换为登录返回的 `access_token`。
- Token 当前有效期 60 分钟，过期后重新登录。JWT 内不存密码；角色从数据库读取。
- 登录接口接受 JSON，不是表单。调用登录成功后，Swagger 不会自动替你授权；点击 Authorize 并只粘贴 Token，不加引号和 `Bearer ` 前缀。
- 请求地址按本文精确填写，不额外增加末尾斜杠。
- 列表响应直接是数组，不是 `{items: ...}`，也没有总条数 `total` 字段。
- 列表接口通用查询参数：`offset` 默认 0 且不能为负；`limit` 默认 20，范围 1～100。
- 示例编号仅用于说明，应使用实际响应中的编号。`task_id` 是任务编号；审核和重交路径使用的是成果记录的 `id`。

## 3. 全部已实现接口

前端调用依据是“HTTP 方法 + 路径”，不是直接调用 Python 函数。函数名称仅方便定位代码；自动生成的 OpenAPI operationId 不是 URL。

| 功能名称 | HTTP 方法 | 路径 | 权限 | 成功状态 | Python 函数 |
| --- | --- | --- | --- | --- | --- |
| 服务首页 | GET | `/` | 无需登录 | 200 | `root` |
| 健康检查 | GET | `/health` | 无需登录 | 200 | `health` |
| 登录 | POST | `/api/auth/login` | 无需登录 | 200 | `login` |
| 获取当前用户 | GET | `/api/auth/me` | 已登录 | 200 | `get_me` |
| 创建任务 | POST | `/api/tasks` | 教师 | 201 | `create_task` |
| 获取任务列表 | GET | `/api/tasks` | 已登录 | 200 | `list_tasks` |
| 获取任务详情 | GET | `/api/tasks/{task_id}` | 已登录 | 200 | `get_task` |
| 提交成果 | POST | `/api/submissions` | 学生 | 201 | `create_submission` |
| 获取自己的成果 | GET | `/api/submissions/mine` | 学生 | 200 | `list_my_submissions` |
| 修改并重交成果 | PUT | `/api/submissions/{submission_id}` | 学生且拥有该记录 | 200 | `update_my_submission` |
| 获取待审核成果 | GET | `/api/reviews/pending` | 教师 | 200 | `list_pending_submisssions` |
| 审核成果 | POST | `/api/reviews/{submission_id}` | 教师 | 200 | `review_one_submission` |

当前待审核列表函数名中的 `submisssions` 确实有三个 s，是源代码现状；不影响 HTTP 路径，前端无需依赖这个拼写。

辅助文档路径为 `/docs`、`/redoc`、`/openapi.json`。它们不是业务接口。

## 4. 请求体与响应字段

### 登录和当前用户

登录请求字段：`username` 长度 1～50；`password` 长度 1～128。账号由初始化脚本创建，设置密码时要求 8～128 字符。用户名与密码不自动去除首尾空格。

成功响应：`access_token: string`、`token_type: "bearer"`。密码错误或账号不存在均返回 401。

`GET /api/auth/me` 无请求体，返回：

```json
{"id":2,"username":"student","role":"student"}
```

`role` 当前为 `student` 或 `teacher`；响应不会包含密码哈希。

### 创建和查看任务

`POST /api/tasks` 请求示例：

```json
{"title":"完成函数练习","description":"编写三个函数并记录测试结果"}
```

- `title`：必填，去除首尾空白后长度 1～100。
- `description`：可选，默认空字符串，最多 2000 字符。
- 成功响应为一个任务对象：`id`、`title`、`description`。
- `GET /api/tasks?offset=0&limit=20` 返回任务对象数组，按任务编号升序。
- `GET /api/tasks/{task_id}` 返回一个任务对象，不存在返回 404。
- 创建任务不接受前端指定任务编号、教师身份或积分值。

### 创建成果

`POST /api/submissions` 请求示例：

```json
{"task_id":1,"content":"完成三个函数，已验证正常输入和空输入"}
```

- `task_id`：必填正整数，必须对应已存在任务。
- `content`：必填，去除首尾空白后长度 1～2000。
- 提交者从 Token 获取；请求不能加入 `student_id`、`status`、`feedback`。
- 任务不存在返回 404；同一学生重复创建同一任务的成果返回 409。

创建、重交、审核的成功响应都采用同一种成果对象：

```json
{
  "id":3,
  "task_id":1,
  "student_id":2,
  "content":"完成三个函数，已验证正常输入和空输入",
  "status":"pending",
  "feedback":""
}
```

`GET /api/submissions/mine?offset=0&limit=20` 返回当前学生的成果数组，按成果编号降序。没有单独的成果详情接口，也没有查询他人成果的学生接口。

### 教师审核

`GET /api/reviews/pending?offset=0&limit=20` 返回状态为 `pending` 的成果数组。当前未显式设置排序，不应依赖其顺序作为稳定业务约定；返回的是学生编号，没有学生姓名。

`POST /api/reviews/{submission_id}` 请求示例：

```json
{"decision":"rejected","feedback":"请补充空输入测试的运行结果"}
```

- `decision`：只能为 `approved` 或 `rejected`。
- `feedback`：必填，去除首尾空白后长度 1～2000。
- 请求里的 `decision` 值被写入数据库的 `status` 字段，二者字段名不同但值对应。
- 成果不存在返回 404；不处于待审核状态返回 409。
- 通过时填写 `{"decision":"approved","feedback":"测试完整，审核通过"}`。
- 当前没有审核历史列表、按学生姓名搜索或任务专属教师限制。

### 学生修改重交

`PUT /api/submissions/{submission_id}` 请求示例：

```json
{"content":"已补充空输入测试，结果符合预期"}
```

仅接受 `content`，长度 1～2000。只能修改自己的 `rejected` 记录。成功后保持原 `id`，状态变回 `pending`，原反馈清空。不属于本人或记录不存在均返回 404；待审核或已通过记录返回 409。

## 5. 错误处理与状态转换

| HTTP 状态 | 含义 | 前端建议 |
| --- | --- | --- |
| 401 | 未登录、Token 无效/过期，或登录凭据错误 | 登录页面显示错误；受保护接口失效时清理登录态并引导登录 |
| 403 | 身份不具备操作权限 | 提示权限不足，不把它当成网络故障 |
| 404 | 对象不存在，或重交对象不属于当前学生 | 提示记录不可用并刷新 |
| 409 | 重复提交、状态已经改变或不允许重交 | 刷新记录，避免盲目重试 |
| 422 | 请求参数或字段不合格 | 显示对应字段的校验提示 |
| 500 | 意外服务端异常 | 查看后端终端日志，不能直接提示“成功” |

业务错误通常返回 `{"detail":"错误说明"}`；422 的 `detail` 通常是错误数组。前端不能假设所有 `detail` 都是字符串。当前提示有英文，界面可按状态码及字段转换成中文，但不要依赖错误文字进行关键业务判断。

状态转换：首次提交为 `pending`；教师可把 `pending` 改为 `approved` 或 `rejected`；学生仅能把自己的 `rejected` 修改重交为 `pending`。当前 `approved` 不允许再审核或重交。

## 6. 已验证范围与 B 同学后续责任

隔离验收已覆盖学生/教师登录、任务发布权限、提交身份防伪、仅查看本人记录、重复提交限制、退回重交、审核通过、重复审核阻止、空反馈校验。最终复测通过 10 项接口检查及状态断言，实际数据库未被测试改动。

这些临时测试尚未保存到仓库测试文件；也不等于已完成前端浏览器联调、负载测试、完整断网演示或落盘数据库重启验收。

B 同学剩余协作事项：

1. 与 A 确认代理/跨域方案、接口地址和错误处理。
2. 与 C 协调共享模型和审核事务；当前审核函数在 `services/learning.py` 内提交事务，积分接入不能在另一个已提交事务中补发。
3. 复查合并后的权限、数据库迁移和回归测试。
4. 保持本接口清单与代码同步，不把尚未实现的积分接口写入已完成清单。
