# ProgramEngineering｜学习激励与协作平台

本项目面向软件工程师项目，围绕学习任务、成果提交、教师反馈与积分激励构建学习协作流程。积分发放与奖励兑换已由 C 同学实现，前端页面待开发联调。

当前阶段：**后端业务（学习流程 + 积分兑换）已完成，28 个自动化测试全部通过；前端待开发、联调。** 本项目仍是本地演示版，不是已上线的完整平台。

## 目前可以做什么

- 使用学生、教师测试账号登录，通过 JWT 验证身份。
- 教师发布任务，登录用户查看任务。
- 学生提交文字成果，并且只能查询、修改自己的成果。
- 教师查看待审核成果，填写反馈并选择通过或退回。
- 学生修改被退回的成果并重新提交；已通过的成果不允许再修改。
- 教师审核通过时自动发放积分（与审核同一事务，重复审核不会重复发放）；学生查看本人积分余额与流水。
- 学生用积分兑换奖励（携带幂等键，网络重试不会重复扣费），可取消未使用的兑换，积分与库存自动返还。
- 使用 SQLite 保存账号、任务、提交状态、积分流水、奖励与兑换单。
- 运行 28 个回归测试与数据对账脚本。

完整流程：登录 → 教师发布任务 → 学生提交 → 教师审核 → 审核通过获得积分 → 兑换奖励（可取消）→ 学生查看反馈 → 被退回后修改重交。

## 三人分工与文档入口

以下 A/B/C 是分工代号，不是姓名。

| 成员 | 负责范围 | 交接文档 |
| --- | --- | --- |
| B：当前后端开发者 | 登录、身份权限、任务、成果提交、审核与重交 | [后端完成情况与接口清单](docs/backend-handoff.md) |
| A：前端同学 | React + TypeScript + Vite 页面与接口联调 | [前端待完成任务](docs/frontend-tasks.md) |
| C：数据与积分同学 | 积分、奖励兑换、数据库扩展、自动化测试 | [数据与积分实现说明](docs/data-points-implementation.md)；原始待办见 [数据与积分任务](docs/data-points-tasks.md) |

## 技术栈与目录

- 已使用：Python 3.11、FastAPI、SQLModel、SQLite、PyJWT、pwdlib/Argon2；测试使用 pytest 与 httpx。
- 前端计划使用：React、TypeScript、Vite；目前尚未初始化。
- 当前不需要 Redis、向量数据库或外部大模型服务。

```text
ProgramEngineering/
├── README.md
├── docs/                   三份交接文档 + 数据与积分实现说明
├── frontend/               前端预留目录，目前只有占位文件
└── backend/
    ├── README.md           后端详细运行说明
    ├── requirements.txt    Python 依赖
    ├── app/                API、模型、权限及业务逻辑
    ├── scripts/            seed.py 创建测试账号；seed_rewards.py 初始化演示奖励；check_data.py 积分对账
    ├── data/               本地 SQLite 数据库，不提交 Git
    └── tests/              回归测试（28 个用例，pytest 运行）
```

## 启动后端

在 Windows PowerShell 中进入项目根目录，再执行：

```powershell
cd backend
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt --timeout 120
.\.venv\Scripts\python.exe -c "import secrets; print('JWT_SECRET_KEY=' + secrets.token_hex(32))"
```

已有可用虚拟环境时跳过创建步骤。将最后一条命令输出的整行内容保存到 `backend/.env`；已有密钥时不要覆盖，否则原有 Token 会失效。密钥不上传、不写入共享文档。

然后在 `backend` 目录运行：

```powershell
.\.venv\Scripts\python.exe -m scripts.seed
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

初始化脚本会提示设置 `teacher` 和 `student` 的密码；输入密码时终端不显示字符。已有账号会跳过，不会重置密码。

初始化奖励演示数据（幂等，可重复执行）：

```powershell
.\.venv\Scripts\python.exe -m scripts.seed_rewards
```

运行回归测试（28 个用例，使用隔离内存库，不影响本地数据）：

```powershell
.\.venv\Scripts\python.exe -m pytest
```

- [健康检查](http://127.0.0.1:8000/health)
- [交互式接口文档](http://127.0.0.1:8000/docs)
- [OpenAPI 定义](http://127.0.0.1:8000/openapi.json)

后续日常启动只需运行最后一条 Uvicorn 命令。更多说明见 [后端 README](backend/README.md)。

## 当前限制与后续工作

- 尚未实现前端页面；前端联调需要开发代理或由后端配置允许的前端来源（积分接口契约见[实现说明](docs/data-points-implementation.md)）。
- 没有注册、找回密码、文件上传、自动续期、服务端注销接口。
- 任务是共享的，没有班级隔离；所有教师都可审核待审核成果。
- 仅保存成果当前内容与反馈，没有完整修改历史、审核人和审核时间记录。
- 兑换单暂无管理员核销流程（当前仅 active / cancelled 两态），按交接文档"先做积分正确性、不做复杂商城"暂缓。
- 现有依赖尚未锁定版本；数据库新增表由 create_all 自动创建（已测试兼容旧库），修改现有表结构时仍需先准备迁移方案。
- 业务在依赖安装完成后可本地运行，不调用外部 AI；但当前 `/docs` 的界面资源默认来自 CDN，不能承诺该页面断网仍可加载。离线演示前应准备本地前端及其资源并实测。
- `.env`、`.venv`、数据库文件不得提交 Git；默认只监听本机，不应直接作为公网生产服务部署。

## 验收状态

后端已有可运行的自动化测试套件：在 `backend` 目录运行 `pytest`，28 个用例全部通过，覆盖登录与角色权限、提交查重、审核状态转换、审核发分恰好一次、积分写入失败整体回滚、兑换一致性与幂等、并发兑换不超卖、重启落盘、旧库升级不破坏数据。数据一致性另由 `scripts/check_data.py` 对账兜底。

此前一轮的隔离数据库人工验收（登录、权限、提交、退回、重交、通过、防重复操作与输入校验）已被上述测试套件固化。前端端到端联调由 A/B/C 共同完成。

## 协作约定

- 接口字段和路径以 [后端交接文档](docs/backend-handoff.md) 与实际 OpenAPI 为准；修改前先同步调用方。
- A 主要修改前端；C 的积分实现复用现有登录和数据库连接，不另建第二套用户系统。
- `models.py`、`schemas.py`、`main.py`、`services/learning.py` 是共享修改点，修改前说明范围，避免互相覆盖。
- 教师审核通过与发积分在同一个数据库事务中完成（已实现并测试锁定）；前端在积分联调完成前不得自行展示积分数字以外的发放状态。
- 不通过删除现有数据库解决迁移问题；先备份、评估迁移，再测试。
