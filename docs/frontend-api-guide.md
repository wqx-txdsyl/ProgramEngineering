# 前端接口接入手册（B + C 全量后端）

核对日期：2026-09-26。依据当前本地路由、请求/响应模型、权限依赖、业务服务与运行时 OpenAPI 编写，包含 21 个业务接口和 2 个基础接口。包含任务标题修改、描述修改、学习进度统计、本人待审核成果查询及学生注册。

本文是当前前端联调的集中入口。旧分工文档中“积分未实现”“测试文件为空”等描述不代表当前版本。拉取本次更新后，应同时使用配套后端代码与本文档。示例 ID、时间、内容均为演示值，实际调用应使用接口返回的 ID。

## 1. 最快接入

### 1.1 后端地址和账号

- 后端默认地址：`http://127.0.0.1:8000`。
- 健康检查：[GET /health](http://127.0.0.1:8000/health)。
- 在线调试：[Swagger /docs](http://127.0.0.1:8000/docs)。
- 机器可读契约：[OpenAPI /openapi.json](http://127.0.0.1:8000/openapi.json)。OpenAPI 目前不会完整列出业务异常和兑换重试的 200 响应，相关说明以本文各接口为准。
- 账号由后端初始化脚本创建，默认用户名为 `teacher`、`student`，密码由初始化人员自行设置，没有统一默认密码。
- 学生也可以通过 `POST /api/auth/register` 自助注册；公开注册不能创建教师。注册成功后仍需单独登录。
- 新电脑需要安装后端依赖、配置本地密钥、初始化本地账号，参见 [后端运行说明](../backend/README.md) 的安装、密钥和账号章节；不要复制或索要同学的 JWT 密钥。

已完成环境配置后，在项目的 `backend` 目录启动：

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

需要演示奖励且尚未初始化时，由后端人员在同一目录执行：

```powershell
.\.venv\Scripts\python.exe -m scripts.seed_rewards
```

该脚本新增演示奖励，已有同 ID 奖励会跳过；它不是 HTTP 接口。奖励中的 AI 提示、资料包等只是兑换演示，没有真实 AI 额度发放或下载交付接口。

### 1.2 React + Vite 本地代理

当前后端没有配置 CORS。从另一个端口的网页直接请求 `http://127.0.0.1:8000/api/...`，可能被浏览器跨域策略阻止。建议开发时让前端请求相对路径 `/api/...`，通过 Vite 转发。

下面是标准 React + Vite 项目的配置示例；已有配置时合并 `server.proxy`，保留同学自己的插件和其他设置，不要整份覆盖。这里故意不设置路径重写，因为后端路径本来就带 `/api`。

```ts
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
      "/health": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
    },
  },
});
```

配置后重启前端开发服务。该配置服务于开发服务器，生产构建部署时需另行配置同源反向代理或后端允许的跨域来源。[Vite 官方代理说明](https://vite.dev/config/server-options#server-proxy)。

默认后端只监听本机；另一位同学电脑上的 `127.0.0.1` 指向他自己的电脑，不会访问你的电脑。建议各自本机运行后端，或由团队另行确认局域网监听地址、防火墙与代理目标。

### 1.3 登录顺序

1. `POST /api/auth/login`，发送 JSON 用户名和密码。
2. 读取返回的 `access_token`，后续请求放在 `Authorization: Bearer <access_token>` 中。
3. `GET /api/auth/me` 获取 `id`、`username`、`role`，根据角色展示学生/教师页面。
4. Token 当前有效期为 60 分钟。没有续期接口；过期后重新登录。
5. 退出登录只清除前端保存的 token 和用户状态；当前没有服务端撤销 token 的注销接口。

`<access_token>` 是说明用占位符，实际发送登录返回的完整字符串，不包含尖括号，不要重复拼接两次 `Bearer`。不要把 token 或密码提交到 Git。

## 2. 全部接口速查

“登录”指学生、教师均可；“学生/教师”指必须为对应角色，教师不能调用学生专用接口。

| 编号 | 方法 | 完整路径 | 权限 | 用途 | 成功响应 |
| --- | --- | --- | --- | --- | --- |
| 01 | POST | `/api/auth/login` | 公开 | 登录 | 200，TokenRead |
| 02 | GET | `/api/auth/me` | 登录 | 当前用户 | 200，UserRead |
| 03 | POST | `/api/tasks` | 教师 | 新建任务 | 201，TaskRead |
| 04 | GET | `/api/tasks` | 登录 | 任务列表 | 200，TaskRead[] |
| 05 | GET | `/api/tasks/{task_id}` | 登录 | 任务详情 | 200，TaskRead |
| 06 | PATCH | `/api/tasks/{task_id}` | 教师 | 修改标题 | 200，TaskRead |
| 07 | PATCH | `/api/tasks/{task_id}/description` | 教师 | 修改描述 | 200，TaskRead |
| 08 | POST | `/api/submissions` | 学生 | 首次提交成果 | 201，SubmissionRead |
| 09 | GET | `/api/submissions/mine` | 学生 | 我的成果列表 | 200，SubmissionRead[] |
| 10 | PUT | `/api/submissions/{submission_id}` | 学生 | 修改被退回的成果并重交 | 200，SubmissionRead |
| 11 | GET | `/api/submissions/me` | 学生 | 我的学习进度统计 | 200，LearningProgressRead |
| 12 | GET | `/api/reviews/pending` | 教师 | 全部待审核成果 | 200，SubmissionRead[] |
| 13 | POST | `/api/reviews/{submission_id}` | 教师 | 审核成果 | 200，SubmissionRead |
| 14 | GET | `/api/points/me` | 学生 | 我的积分余额 | 200，PointBalanceRead |
| 15 | GET | `/api/points/transactions` | 学生 | 我的积分流水 | 200，PointTransactionRead[] |
| 16 | GET | `/api/rewards` | 登录 | 已上架奖励列表 | 200，RewardRead[] |
| 17 | POST | `/api/rewards/{reward_id}/redeem` | 学生 | 兑换奖励 | 201 新建 / 200 重复请求，RedemptionRead |
| 18 | GET | `/api/rewards/redemptions/mine` | 学生 | 我的兑换记录 | 200，RedemptionRead[] |
| 19 | POST | `/api/rewards/redemptions/{redemption_id}/cancel` | 学生 | 取消自己的兑换 | 200，RedemptionRead |
| 20 | GET | `/` | 公开 | 后端提示 | 200，对象 |
| 21 | GET | `/health` | 公开 | 健康检查 | 200，对象 |
| 22 | POST | `/api/auth/register` | 公开 | 注册学生账号 | 201，UserRead |
| 23 | GET | `/api/submissions/mine/pending` | 学生 | 我的待审核成果 | 200，SubmissionRead[] |

## 3. 所有接口通用约定

### 3.1 请求格式

- 有请求体的接口统一发送 JSON，设置 `Content-Type: application/json`，不是表单或文件上传。
- 除注册、登录、根路径、健康检查外，都需要 Bearer token。
- 路径中的 `{task_id}`、`{submission_id}`、`{reward_id}`、`{redemption_id}` 必填且为整数；使用实际返回的记录 ID。非整数会触发 422。目前路径参数没有额外声明正数限制；不存在的 ID 按对应业务返回 404。
- 下文没有列出的查询参数不具备筛选能力。例如传入 `student_id` 不会让“我的记录”变成别人的记录；传入 `status` 不会自动筛选。
- 请求体都禁止额外字段。不要把完整响应对象原样提交回去，不要额外传 `id`、`student_id`、`status`、`balance`、`role` 等未经声明的字段。
- 除登录外，当前请求体中的普通字符串字段（title、description、content、feedback、request_key）会去掉两端空白，再检查长度；中间空格不会被全部删除。枚举字段 decision 必须精确传 `approved` 或 `rejected`，不要附加空格。
- 注册及登录的用户名、密码不自动去掉空白。注册用户名不允许空格；密码允许标点和空格，前端不能擅自修改用户输入的密码。
- 所有表单必填字段均不能为 `null`。新建任务的 `description` 可省略或传空字符串，但不能传 `null`。

### 3.2 分页

以下七个接口支持相同的分页参数：任务列表、我的成果列表、我的待审核成果、教师待审核列表、积分流水、奖励列表、我的兑换记录。

| 参数 | 位置 | 类型 | 必填 | 默认值 | 范围 | 含义 |
| --- | --- | --- | --- | --- | --- | --- |
| offset | query | integer | 否 | 0 | ≥ 0 | 跳过前面多少条 |
| limit | query | integer | 否 | 20 | 1～100 | 最多返回多少条 |

例如 `?offset=20&limit=20` 获取下一批。页码从 1 开始时，`offset = (page - 1) * pageSize`。

所有列表直接返回数组，没有 `{data: ...}`、`items`、`total` 或 `has_more` 外层包装。没有记录返回 `[]`，不是 404。返回数量小于 `limit` 时可判断本次已到末尾；刚好等于 `limit` 不代表一定还有下一页。数据变动时应重新刷新，不能把 offset 分页当作稳定快照。

### 3.3 字段和响应结构

以下为可复用 TypeScript 类型，字段名与后端一致。`role`、`status`、`source_type` 在当前响应 schema 中是字符串，具体已实现取值在后文说明，不要从未声明的字段猜测含义。

```ts
export interface TokenRead {
  access_token: string;
  token_type: string;
}

export interface UserRead {
  id: number;
  username: string;
  role: string;
}

export interface TaskRead {
  id: number;
  title: string;
  description: string;
}

export interface SubmissionRead {
  id: number;
  task_id: number;
  student_id: number;
  content: string;
  status: string;
  feedback: string;
}

export interface LearningProgressRead {
  submitted_count: number;
  approved_count: number;
}

export interface PointBalanceRead {
  user_id: number;
  balance: number;
}

export interface PointTransactionRead {
  id: number;
  user_id: number;
  change: number;
  source_type: string;
  source_id: number;
  created_at: string;
}

export interface RewardRead {
  id: number;
  name: string;
  description: string;
  cost: number;
  stock: number;
  is_active: boolean;
}

export interface RedemptionRead {
  id: number;
  user_id: number;
  reward_id: number;
  cost: number;
  status: string;
  request_key: string;
  created_at: string;
}
```

- `TaskRead.id` 是任务 ID；`SubmissionRead.id` 是成果 ID，审核和重交用后者，不能混用。
- `submitted_count`、`approved_count` 为非负整数，`balance` 表示积分，不是人民币或 token 数。
- `change` 是有符号积分变化，正数增加、负数扣除。
- `cost` 为本次兑换消耗的积分；兑换记录中的 cost 是保存的历史值。
- `created_at` 为 UTC ISO 8601 字符串，例如 `2026-09-26T08:00:00+00:00`。可以用 `new Date(value).toLocaleString()` 显示用户本地时间。
- 当前任务和提交响应没有创建时间、审核时间、审核人、学生姓名、任务标题嵌套对象。

## 4. 登录与用户（B）

### 01 · POST /api/auth/login

权限：公开。路径参数：无。查询参数：无。请求体模型：`LoginRequest`。

| 字段 | 类型 | 必填 | 限制 |
| --- | --- | --- | --- |
| username | string | 是 | 1～50 字符，不自动去空白 |
| password | string | 是 | 1～128 字符，不自动去空白 |

请求示例（密码仅为虚构示例，需替换为本地账号实际密码）：

```http
POST /api/auth/login
Content-Type: application/json

{"username":"student","password":"example-password"}
```

成功 200：

```json
{"access_token":"example-token-not-valid","token_type":"bearer"}
```

上面的 token 是无效演示值，联调必须读取真实登录响应。用户名不存在或密码错误：401，`Invalid username or password`。字段缺失、超长或多传字段：422。

### 02 · GET /api/auth/me

权限：登录。路径参数、查询参数、请求体：均无。

```http
GET /api/auth/me
Authorization: Bearer <access_token>
```

成功 200：

```json
{"id":2,"username":"student","role":"student"}
```

当前系统使用 `student`、`teacher` 两种角色。角色从数据库读取，不是前端选择后上报，也不是直接信任 token 中的角色字段。不要尝试通过修改浏览器状态提升权限。

### 22 · POST /api/auth/register

权限：公开，不需要 token。路径参数、查询参数：无。请求体模型：`Register`。

| 字段 | 类型 | 必填 | 限制 |
| --- | --- | --- | --- |
| username | string | 是 | 3～50 字符，只允许英文字母、数字、下划线，规则 `^[a-zA-Z0-9_]+$` |
| password | string | 是 | 8～128 字符，允许标点和空格，不自动修剪 |

```http
POST /api/auth/register
Content-Type: application/json

{"username":"student_new","password":"Example!password123"}
```

成功 201：

```json
{"id":3,"username":"student_new","role":"student"}
```

- 仅接收 username、password；额外传入 role、id、password_hash 会返回 422。
- 后端固定创建 student 角色，密码哈希入库；响应不包含密码、密码哈希或 token。
- 用户名已存在返回 409，detail 为 `Username has been registered`。保存时发生用户名唯一约束冲突，也会回滚并重新确认重复情况。
- 其他输入校验错误返回 422。注册失败时不能把页面直接切换到已登录状态。
- 注册成功后调用 `/api/auth/login`，使用相同用户名和原始密码登录，取得 token 后再查询 `/api/auth/me`。
- 当前没有注册限流、验证码、邮箱验证或找回密码功能；这是本地演示版公开注册能力，不应未经加固直接开放公网。

## 5. 任务（B）

以下受保护接口的请求示例省略 Authorization 行，实际必须携带对应角色的 token；所有 JSON 请求体均需设置 Content-Type。

### 03 · POST /api/tasks

权限：教师。路径参数、查询参数：无。请求体模型：`TaskCreate`。

| 字段 | 类型 | 必填 | 限制 / 默认 |
| --- | --- | --- | --- |
| title | string | 是 | 去两端空白后 1～100 字符 |
| description | string | 否 | 去两端空白后 0～2000 字符，默认 `""` |

```http
POST /api/tasks
Content-Type: application/json

{"title":"学习数据库","description":"完成查询练习并提交学习成果"}
```

成功 201：

```json
{"id":7,"title":"学习数据库","description":"完成查询练习并提交学习成果"}
```

学生调用返回 403，输入不合法返回 422。任务是共享的，没有创建者归属或班级隔离。

### 04 · GET /api/tasks

权限：登录。路径参数：无。查询参数：通用 `offset`、`limit`。请求体：无。按任务 ID 升序。

```http
GET /api/tasks?offset=0&limit=20
```

成功 200：

```json
[{"id":7,"title":"学习数据库","description":"完成查询练习并提交学习成果"}]
```

没有关键字搜索、状态筛选或按学生筛选参数。

### 05 · GET /api/tasks/{task_id}

权限：登录。路径参数：`task_id`，必填整数。查询参数、请求体：无。

```http
GET /api/tasks/7
```

成功 200：

```json
{"id":7,"title":"学习数据库","description":"完成查询练习并提交学习成果"}
```

任务不存在：404，`Task Not Found`。

### 06 · PATCH /api/tasks/{task_id}

权限：教师。路径参数：`task_id`，必填整数。查询参数：无。请求体模型：`TaskRename`。

| 字段 | 类型 | 必填 | 限制 |
| --- | --- | --- | --- |
| title | string | 是 | 去两端空白后 1～100 字符 |

```http
PATCH /api/tasks/7
Content-Type: application/json

{"title":"完成数据库学习"}
```

成功 200，返回完整任务，description 不变：

```json
{"id":7,"title":"完成数据库学习","description":"完成查询练习并提交学习成果"}
```

任务不存在：404，`Task Not Found`。不能在这个接口顺便传 description；多传字段返回 422。

### 07 · PATCH /api/tasks/{task_id}/description

权限：教师。路径参数：`task_id`，必填整数。查询参数：无。请求体模型：`TaskDescriptionUpdate`。

| 字段 | 类型 | 必填 | 限制 |
| --- | --- | --- | --- |
| description | string | 是 | 去两端空白后 1～2000 字符 |

```http
PATCH /api/tasks/7/description
Content-Type: application/json

{"description":"增加一段关于事务的学习总结"}
```

成功 200，返回完整任务，title 不变：

```json
{"id":7,"title":"完成数据库学习","description":"增加一段关于事务的学习总结"}
```

任务不存在：404，`Task Not Found`。注意：新建任务允许空描述，但当前修改描述接口不允许清空；空字符串或全空白返回 422。标题和描述需分两次修改，当前没有合并更新接口，两次请求也不是一个原子操作。

## 6. 学生成果与进度（B）

### 08 · POST /api/submissions

权限：学生。路径参数、查询参数：无。请求体模型：`SubmissionCreate`。

| 字段 | 类型 | 必填 | 限制 |
| --- | --- | --- | --- |
| task_id | integer | 是 | > 0，且任务必须存在 |
| content | string | 是 | 去两端空白后 1～2000 字符 |

```http
POST /api/submissions
Content-Type: application/json

{"task_id":7,"content":"我完成了数据库查询练习"}
```

成功 201：

```json
{"id":12,"task_id":7,"student_id":2,"content":"我完成了数据库查询练习","status":"pending","feedback":""}
```

- `student_id` 由登录身份确定；初始状态 `pending`、初始反馈空字符串由后端设置。
- 任务不存在：404，`Task not found`。
- 同一个学生对同一个任务只能有一条提交记录，无论该记录是什么状态，再次 POST 都返回 409，`You have already submitted for this task`。
- 被退回后重交请调用下面的 PUT，不要再次 POST。

### 09 · GET /api/submissions/mine

权限：学生。路径参数：无。查询参数：通用 `offset`、`limit`。请求体：无。仅当前学生全部状态的提交，按提交 ID 降序。

```http
GET /api/submissions/mine?offset=0&limit=20
```

成功 200：

```json
[{"id":12,"task_id":7,"student_id":2,"content":"我完成了数据库查询练习","status":"pending","feedback":""}]
```

没有提交详情 GET 接口；成果正文、状态、反馈从此列表获取。没有服务端 `task_id` 或 `status` 筛选参数；如需前端过滤，注意只能过滤已加载的数据，不能把一页记录当作全部记录。

### 10 · PUT /api/submissions/{submission_id}

权限：学生，且必须是该提交的所有者。路径参数：`submission_id`，必填整数。查询参数：无。请求体模型：`SubmissionUpdate`。

| 字段 | 类型 | 必填 | 限制 |
| --- | --- | --- | --- |
| content | string | 是 | 去两端空白后 1～2000 字符 |

```http
PUT /api/submissions/12
Content-Type: application/json

{"content":"已根据反馈补充事务和回滚的说明"}
```

成功 200：

```json
{"id":12,"task_id":7,"student_id":2,"content":"已根据反馈补充事务和回滚的说明","status":"pending","feedback":""}
```

仅 `rejected` 状态能重交。成功时沿用原提交 ID，状态变回 `pending`，旧 feedback 清空。任务 ID 和学生 ID 不变。当前没有历史版本保存。

- 记录不存在或属于其他学生：404，`Submission not found`。
- 当前不是 rejected：409，`Submission cannot be resubmitted`。

### 11 · GET /api/submissions/me

权限：学生。路径参数、查询参数、请求体：均无。

```http
GET /api/submissions/me
```

成功 200：

```json
{"submitted_count":3,"approved_count":1}
```

`submitted_count` 是当前学生的全部提交记录数量，包含 pending、approved、rejected；不是点击提交的次数，重交同一条记录不会增加它。`approved_count` 仅统计当前状态为 approved 的记录。没有记录时两项都为 0。

该统计针对全部记录，不受列表分页影响。不返回任务总数、完成率、待审核数量或退回数量，也不能拿它推算“已完成任务占全部任务比例”。实际路径是 `/api/submissions/me`，不是 `/api/progress/me` 或 `/api/submissions/me/progress`。

### 23 · GET /api/submissions/mine/pending

权限：学生。路径参数：无。查询参数：通用 `offset`、`limit`。请求体：无。只返回当前学生 status=pending 的提交，按提交 ID 降序。

```http
GET /api/submissions/mine/pending?offset=0&limit=20
```

成功 200：

```json
[{"id":12,"task_id":7,"student_id":2,"content":"我完成了数据库查询练习","status":"pending","feedback":""}]
```

没有待审核记录或超出分页范围时返回 `[]`。不会包含其他学生的记录，也不会包含自己的 approved 或 rejected 记录；传入 student_id 不会改变查询归属。未登录 401、教师访问 403，非法分页参数 422。此接口是学生自己的待审核列表，与教师使用的 `/api/reviews/pending` 区分。

## 7. 教师审核（B，与 C 的发分逻辑联动）

### 12 · GET /api/reviews/pending

权限：教师。路径参数：无。查询参数：通用 `offset`、`limit`。请求体：无。

```http
GET /api/reviews/pending?offset=0&limit=20
```

成功 200：

```json
[{"id":12,"task_id":7,"student_id":2,"content":"已根据反馈补充事务和回滚的说明","status":"pending","feedback":""}]
```

返回所有学生的 pending 提交，没有班级、任务创建教师等隔离条件。当前查询没有显式排序，不要假设一定最新优先。审核后记录会离开该列表，建议重新从 offset=0 刷新，避免列表缩短后跳过记录。

显示任务名称可根据 `task_id` 查询任务详情或使用已有任务缓存；当前没有“按学生 ID 获取姓名”的接口，可以先显示 student_id，不能把当前登录教师的用户名当作提交人的姓名。

### 13 · POST /api/reviews/{submission_id}

权限：教师。路径参数：`submission_id`，必填整数。查询参数：无。请求体模型：`ReviewCreate`。

| 字段 | 类型 | 必填 | 限制 |
| --- | --- | --- | --- |
| decision | string | 是 | 仅 `approved` 或 `rejected` |
| feedback | string | 是 | 去两端空白后 1～2000 字符，通过和退回都必须填写 |

通过请求：

```http
POST /api/reviews/12
Content-Type: application/json

{"decision":"approved","feedback":"内容完整，审核通过"}
```

成功 200：

```json
{"id":12,"task_id":7,"student_id":2,"content":"已根据反馈补充事务和回滚的说明","status":"approved","feedback":"内容完整，审核通过"}
```

退回请求（这是对待审核记录的另一种选择，不能接着对已经通过的同一记录发送）：

```http
POST /api/reviews/12
Content-Type: application/json

{"decision":"rejected","feedback":"请补充一次具体的查询示例"}
```

退回成功 200：

```json
{"id":12,"task_id":7,"student_id":2,"content":"已根据反馈补充事务和回滚的说明","status":"rejected","feedback":"请补充一次具体的查询示例"}
```

- 请求字段叫 `decision`；响应字段叫 `status`。不能请求 `{"status":"approved"}`。
- 仅 pending 可审核。不存在：404，`Submission not found`；不是 pending：409，`Submission has already been reviewed`。
- 审核通过自动给提交学生增加 **10 积分**，审核和积分写入处于同一个事务；前端不再调用额外发分接口，也不能自己改余额。
- 退回不发积分。已通过不能再次审核或重交。
- 积分重复发放防护冲突：409，`Review reward already issued for this submission`。
- 响应不包含积分余额，学生端后续重新请求 `/api/points/me`。没有实时推送，需要重新加载或主动刷新。

## 8. 积分（C）

### 14 · GET /api/points/me

权限：学生。路径参数、查询参数、请求体：均无。

```http
GET /api/points/me
```

成功 200：

```json
{"user_id":2,"balance":10}
```

尚无积分账户时也返回 200，balance 为 0，不是 404。只能查自己，不接受指定 user_id。教师不能通过此接口查询学生积分。

### 15 · GET /api/points/transactions

权限：学生。路径参数：无。查询参数：通用 `offset`、`limit`。请求体：无。仅当前学生，按流水 ID 降序。

```http
GET /api/points/transactions?offset=0&limit=20
```

成功 200：

```json
[{"id":31,"user_id":2,"change":10,"source_type":"review_approved","source_id":12,"created_at":"2026-09-26T08:00:00+00:00"}]
```

| source_type | 显示建议 | change | source_id 的含义 |
| --- | --- | --- | --- |
| review_approved | 审核通过奖励 | +10 | Submission 的 id |
| redeem | 奖励兑换支出 | 负数 | Redemption 的 id，不是奖励 id |
| refund | 取消兑换退款 | 正数 | Redemption 的 id |

对未来或人工数据中的未知 source_type 保留通用显示，不要让页面崩溃。余额以余额接口为准，不能只把当前一页流水相加当作总余额。

## 9. 奖励与兑换（C）

### 16 · GET /api/rewards

权限：登录。路径参数：无。查询参数：通用 `offset`、`limit`。请求体：无。只返回 `is_active=true` 的奖励，按奖励 ID 升序。

```http
GET /api/rewards?offset=0&limit=20
```

成功 200：

```json
[{"id":1,"name":"专属成就徽章（演示）","description":"个人主页展示的电子徽章","cost":10,"stock":20,"is_active":true}]
```

列表可能包含 stock=0 的已上架奖励，前端应显示售罄并禁用兑换。未初始化奖励时可能返回空数组。没有奖励详情 GET、创建、修改、上下架的 HTTP 接口。

### 17 · POST /api/rewards/{reward_id}/redeem

权限：学生。路径参数：`reward_id`，必填整数。查询参数：无。请求体模型：`RedeemRequest`。

| 字段 | 类型 | 必填 | 限制 |
| --- | --- | --- | --- |
| request_key | string | 是 | 去两端空白后 1～100 字符；同一学生的一次兑换意图使用同一个键 |

```http
POST /api/rewards/1/redeem
Content-Type: application/json

{"request_key":"a4c426a9-68eb-4e18-9954-22a2ceea367e"}
```

首次成功 201：

```json
{"id":5,"user_id":2,"reward_id":1,"cost":10,"status":"active","request_key":"a4c426a9-68eb-4e18-9954-22a2ceea367e","created_at":"2026-09-26T08:05:00+00:00"}
```

每次新兑换购买 1 份，扣除后端奖励价格对应的积分，库存减 1；不接收数量、价格、用户 ID 等其他字段。成功后刷新余额、奖励库存、兑换记录，必要时刷新积分流水。

**request_key 使用规则：**

1. 用户确认一次新兑换时生成一个键，例如在支持的浏览器环境中使用 `crypto.randomUUID()`，并在请求结果明确前保留它。
2. 同一兑换的网络超时重试复用原键，不要在每一次 fetch 内重新生成。
3. 同一学生、相同键、相同奖励的已完成请求再次到达时返回已有兑换单，HTTP 为 200，不再次扣分或扣库存。
4. 相同键改换奖励返回 409。明确购买第二份才生成新键。
5. 已取消的订单用原键重试，会返回那张 `cancelled` 订单，不会重新兑换。要再次购买需使用新键。
6. 前端仍应在请求中禁用重复点击。当前实现没有将所有“同一键同时首次到达”的数据库唯一键竞争转换成友好业务响应；不要刻意并行重复请求。收到 500 或网络错误时先核对记录，再用原键恢复，不能换键盲目重试。

业务错误：

| 状态码 | detail | 含义 |
| --- | --- | --- |
| 404 | Reward not found | 奖励不存在 |
| 409 | Reward is not available | 奖励已下架 |
| 409 | Reward is out of stock | 库存不足 |
| 409 | Insufficient balance | 积分不足 |
| 409 | Request key was already used for a different reward | 同一个键被用于不同奖励 |

### 18 · GET /api/rewards/redemptions/mine

权限：学生。路径参数：无。查询参数：通用 `offset`、`limit`。请求体：无。当前学生的所有状态兑换记录，按兑换 ID 降序。

```http
GET /api/rewards/redemptions/mine?offset=0&limit=20
```

成功 200：

```json
[{"id":5,"user_id":2,"reward_id":1,"cost":10,"status":"active","request_key":"a4c426a9-68eb-4e18-9954-22a2ceea367e","created_at":"2026-09-26T08:05:00+00:00"}]
```

当前没有按兑换 ID 获取详情的 GET 接口，也没有 request_key 查询接口。恢复不确定请求时可以查询记录，或使用原键重试兑换。

兑换记录没有奖励名称；可使用奖励列表缓存按 reward_id 匹配，但下架奖励不会出现在奖励列表。无法匹配时显示“奖励 #ID”，不要假定名称始终能查到。

### 19 · POST /api/rewards/redemptions/{redemption_id}/cancel

权限：学生，只能操作自己的兑换。路径参数：`redemption_id`，必填整数。查询参数、请求体：无。不需要 request_key。

```http
POST /api/rewards/redemptions/5/cancel
```

成功 200：

```json
{"id":5,"user_id":2,"reward_id":1,"cost":10,"status":"cancelled","request_key":"a4c426a9-68eb-4e18-9954-22a2ceea367e","created_at":"2026-09-26T08:05:00+00:00"}
```

只有 active 状态可取消。成功后按兑换记录保存的 cost 退回积分、库存加 1，新增退款流水，状态变为 cancelled。created_at 仍是最初创建时间，不是取消时间。刷新余额、库存、兑换记录和流水。

| 状态码 | detail | 含义 |
| --- | --- | --- |
| 404 | Redemption not found | 不存在或属于他人 |
| 409 | Redemption cannot be cancelled | 当前不是 active，包括已经取消 |
| 409 | Refund already issued for this redemption | 退款唯一性防护冲突 |

重复取消不会重复退款，但不会返回重复成功，而是 409。当前只有 active、cancelled 两个业务状态，没有核销、已使用、发货、下载授权接口；不要将 active 文案写成“已实际发放”。

## 10. 基础接口

### 20 · GET /

权限：公开。路径参数、查询参数、请求体：均无。

```http
GET /
```

成功 200：

```json
{"message":"Backend is active"}
```

这里指后端根路径。Vite 前端的 `/` 是前端页面，不会自动代理到后端根路径。

### 21 · GET /health

权限：公开。路径参数、查询参数、请求体：均无。

```http
GET /health
```

成功 200：

```json
{"status":"ok"}
```

该接口返回固定状态，不执行完整数据库检查，也不能证明登录或兑换流程都正常。

FastAPI 另提供 `/docs`、`/redoc`、`/openapi.json` 等文档辅助路径，不属于上述 23 个应用接口。Swagger 默认使用外部 CDN 资源，不能保证断网后界面能加载。

## 11. 错误处理统一规则

业务异常通常返回：

```json
{"detail":"Insufficient balance"}
```

校验失败返回 detail 数组，例如 limit=0：

```json
{"detail":[{"type":"greater_than_equal","loc":["query","limit"],"msg":"Input should be greater than or equal to 1","input":"0","ctx":{"ge":1}}]}
```

校验错误的具体 msg、input 等可能随依赖版本变化，前端应按结构解析，不要依赖整段英文完全相等。`loc` 的第一个元素可为 body、query、path。

| HTTP 状态 | 前端含义与处理 |
| --- | --- |
| 200 / 201 | 成功；用 `response.ok` 判断，不要只允许 200 |
| 401 | 未登录、token 无效/过期、用户已不存在；受保护接口应清理登录状态并提示重新登录；登录接口 401 表示账号或密码错误 |
| 403 | 当前账号角色不允许操作；保留登录状态，不要反复要求登录 |
| 404 | 目标不存在，或后端为隐藏他人记录而按不存在处理；刷新页面数据 |
| 409 | 重复提交、重复审核、状态变化、积分/库存不足或幂等键冲突；展示提示并刷新相关数据，不盲目重试 |
| 422 | 字段缺失、多传字段、类型/长度/范围错误；提示对应表单或参数 |
| 500 | 服务端异常；可能是纯文本 `Internal Server Error`，不是保证有 detail 的 JSON；联系后端并核对是否已产生结果 |
| 无 HTTP 响应 | 网络、跨域、后端未运行或连接中断；不能当作业务上的 401，也不能认定写请求一定没执行 |

所有受保护接口的常见 401 detail 为 `Please Login to Continue`，角色错误的 403 detail 为 `You do not have permission to access this resource`。输入错误的 422 可发生在任何具有路径、查询或请求体约束的接口。多个条件同时失败时，不要依赖固定的报错优先顺序。

## 12. 可复制的浏览器请求封装

以下是前端接入示例，不是已经添加到前端项目的实现。使用第 1.2 节代理，所有业务路径传完整 `/api/...`，不再额外拼接 `/api`。示例把 token 放在内存中，刷新网页后需重新登录；如果要持久化，应自行评估 XSS 风险，不要把任何浏览器存储当作绝对安全的 token 保险箱。

```ts
type RequestOptions = {
  method?: "GET" | "POST" | "PUT" | "PATCH";
  body?: unknown;
  auth?: boolean;
};

type LoginResult = {
  access_token: string;
  token_type: string;
};

let accessToken: string | null = null;

export function setAccessToken(value: string | null): void {
  accessToken = value;
}

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    message: string,
    public readonly payload: unknown,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

function errorMessage(payload: unknown, fallback: string): string {
  if (typeof payload !== "object" || payload === null || !("detail" in payload)) {
    return fallback;
  }
  const detail = (payload as { detail: unknown }).detail;
  if (typeof detail === "string") return detail;
  if (!Array.isArray(detail)) return fallback;
  const messages = detail.map((item: unknown) => {
    if (typeof item !== "object" || item === null) return "请求参数不合法";
    const issue = item as { loc?: unknown; msg?: unknown };
    const location = Array.isArray(issue.loc) ? issue.loc.map(String).join(".") : "参数";
    const message = typeof issue.msg === "string" ? issue.msg : "不合法";
    return `${location}: ${message}`;
  });
  return messages.join("；") || fallback;
}

export async function apiRequest<T>(
  path: string,
  options: RequestOptions = {},
): Promise<T> {
  const headers = new Headers({ Accept: "application/json" });
  const useAuth = options.auth !== false;
  if (useAuth && accessToken) {
    headers.set("Authorization", `Bearer ${accessToken}`);
  }
  if (options.body !== undefined) {
    headers.set("Content-Type", "application/json");
  }
  const response = await fetch(path, {
    method: options.method ?? "GET",
    headers,
    body: options.body === undefined ? undefined : JSON.stringify(options.body),
  });
  const raw = await response.text();
  let payload: unknown = raw;
  if (raw !== "") {
    try {
      payload = JSON.parse(raw);
    } catch {
      payload = raw;
    }
  }
  if (!response.ok) {
    if (response.status === 401 && useAuth) setAccessToken(null);
    throw new ApiError(
      response.status,
      errorMessage(payload, `请求失败（HTTP ${response.status}）`),
      payload,
    );
  }
  return payload as T;
}

export async function login(username: string, password: string): Promise<LoginResult> {
  setAccessToken(null);
  const result = await apiRequest<LoginResult>("/api/auth/login", {
    method: "POST",
    body: { username, password },
    auth: false,
  });
  setAccessToken(result.access_token);
  return result;
}

export function logout(): void {
  setAccessToken(null);
}
```

`apiRequest<T>` 中的 T 是 TypeScript 静态类型提示，不会在浏览器运行时替你验证 JSON。网络故障会直接抛出 fetch 错误；业务 HTTP 错误抛出 ApiError。调用页面需 catch 并显示消息，不能只写成功分支。

结合第 3.3 节类型，调用方式如下（在 async 页面逻辑或事件函数内执行，调用前已登录）：

```ts
const me = await apiRequest<UserRead>("/api/auth/me");
const tasks = await apiRequest<TaskRead[]>("/api/tasks?offset=0&limit=20");
```

学生提交示例（selectedTaskId 和 content 是页面实际选中的任务 ID 与输入内容）：

```ts
const submission = await apiRequest<SubmissionRead>("/api/submissions", {
  method: "POST",
  body: { task_id: selectedTaskId, content },
});
```

取消示例（redemptionId 来自兑换记录，不是 reward_id）：

```ts
const redemption = await apiRequest<RedemptionRead>(
  `/api/rewards/redemptions/${redemptionId}/cancel`,
  { method: "POST" },
);
```

错误显示示例（error 为 catch 捕获到的值；将 message 放入页面提示）：

```ts
const message = error instanceof Error ? error.message : "请求失败，请稍后重试";
```

## 13. 页面调用顺序与刷新清单

### 学生端

1. 无账号时先注册；注册成功后登录 → 当前用户信息，确认 role=student。
2. 首页可分别获取任务列表、学习进度、积分余额；这些是不同接口，不要等待一个接口返回所有首页信息。
3. 任务详情 → POST 成果；提交后刷新我的成果和学习进度。
4. 我的成果页 → 显示 status 与 feedback；只有 rejected 显示“修改并重交”。重交后刷新成果和进度；“待审核”页签可调用 `/api/submissions/mine/pending`，不需要先加载全部记录再过滤。
5. 成果获批后 → 刷新成果、进度、余额、流水。没有 WebSocket 自动通知。
6. 奖励页 → 奖励列表 + 余额；兑换时保留 request_key；成功后刷新余额、奖励列表、兑换记录、流水。
7. 兑换记录页 → active 可显示取消按钮；取消成功后刷新余额、库存、记录、流水。

### 教师端

1. 登录 → 当前用户信息，确认 role=teacher。
2. 任务列表 → 新建或分开修改标题、描述；保存成功后用返回对象更新页面或重新查询。
3. 待审核列表 → 显示成果内容、学生 ID、任务信息；输入 feedback，选择通过/退回。
4. 审核成功后从 offset=0 刷新待审核列表；收到 409 表示状态已变化，应刷新而不是反复点击通过。
5. 教师没有查询所有用户、任意学生积分、所有审核历史或所有兑换订单的接口，不要给这些按钮绑定猜测出来的 URL。

### 前端按钮与状态

| 对象 | 状态 | 可执行动作 |
| --- | --- | --- |
| Submission | pending | 教师审核；学生等待，不能重交 |
| Submission | rejected | 所属学生 PUT 修改并重交，回到 pending |
| Submission | approved | 展示通过和反馈；当前不允许再次审核或重交 |
| Redemption | active | 所属学生取消 |
| Redemption | cancelled | 展示已取消，不能再次取消；再购买需新 request_key |

按钮禁用只是交互提示，最终权限和状态由后端判断。请求期间禁用提交按钮，结果不明确时核对记录，避免重复写入。

## 14. 当前未提供的能力与联调边界

- 已提供学生注册，但没有公开教师注册、修改密码、找回密码、刷新 token、服务端注销接口。
- 没有任务删除、成果删除、上传附件、图片上传、富文本文件处理接口；content 只是普通字符串，前端不要直接作为不可信 HTML 渲染。
- 没有用户列表、学生详情、班级/团队隔离、任务创建者限制。
- 没有成果详情 GET、审核历史列表、审核人/审核时间、完整修改历史。
- 已提供 `/api/submissions/mine/pending`；不提供通用状态筛选或学生访问全部用户成果的接口。
- 没有 rewards 管理后台接口、积分手动增减接口、兑换核销、真实 AI token/场地/资料交付接口。
- 没有统一列表总数、关键字搜索、请求排序参数或通用 status 筛选；不要把未定义参数当作已实现功能。
- 本手册未修改任何后端业务代码。新功能、字段或路由后续变更时，需要同步更新这份文档并通知调用方。

## 15. 契约核对记录

- 已对照运行时 OpenAPI 核对 23 个应用接口的方法、路径、请求体、查询参数与响应模型。
- 文档中的 36 份请求/响应示例已通过本地运行时模型校验，JSON 代码块均可解析。
- 前一轮使用隔离内存数据库完成 29 次 HTTP 调用，覆盖当时的 21 个应用接口，以及退回、重交、通过发分、兑换重试、取消退款、取消后复用原键返回旧订单等流程；未访问实际业务数据库。
- 新增注册接口已隔离验证正常注册、哈希入库、登录与身份、普通重复用户名及模拟保存时唯一约束冲突；其他约束异常会回滚并继续抛出。本人待审核列表已隔离验证归属、状态、排序、分页、空结果、权限和参数限制。
- 额外对照权限依赖与业务服务补充 401/403/404/409、审核发分、退款、重试与状态变化规则。
- 本轮之前：原有 28 项隔离测试通过；新学习进度接口的 7 项隔离检查通过。该记录不等同于前端端到端测试已经完成。
- 文档中的演示 ID、token、密码、时间不是可直接复用的真实数据库凭据。
