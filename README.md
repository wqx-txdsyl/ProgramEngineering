# ProgramEngineering｜学习激励与协作平台

本项目面向软件工程师项目，围绕学习任务、成果提交和教师反馈构建基础学习协作流程。后续由团队接入积分奖励与兑换功能。

当前阶段：**后端基础业务已完成，前端和积分兑换待开发、联调。** 本项目仍是本地演示版，不是已上线的完整平台。

## 目前可以做什么

- 使用学生、教师测试账号登录，通过 JWT 验证身份。
- 教师发布任务，登录用户查看任务。
- 学生提交文字成果，并且只能查询、修改自己的成果。
- 教师查看待审核成果，填写反馈并选择通过或退回。
- 学生修改被退回的成果并重新提交；已通过的成果不允许再修改。
- 使用 SQLite 保存账号、任务和当前提交状态。

完整流程：登录 → 教师发布任务 → 学生提交 → 教师审核 → 学生查看反馈 → 被退回后修改重交。

## 三人分工与文档入口

以下 A/B/C 是分工代号，不是姓名。

| 成员 | 负责范围 | 交接文档 |
| --- | --- | --- |
| B：当前后端开发者 | 登录、身份权限、任务、成果提交、审核与重交 | [后端完成情况与接口清单](docs/backend-handoff.md) |
| A：前端同学 | React + TypeScript + Vite 页面与接口联调 | [前端待完成任务](docs/frontend-tasks.md) |
| C：数据与积分同学 | 积分、奖励兑换、数据库扩展、自动化测试 | [数据与积分待完成任务](docs/data-points-tasks.md) |

## 技术栈与目录

- 已使用：Python 3.11、FastAPI、SQLModel、SQLite、PyJWT、pwdlib/Argon2。
- 前端计划使用：React、TypeScript、Vite；目前尚未初始化。
- 当前不需要 Redis、向量数据库或外部大模型服务。

```text
ProgramEngineering/
├── README.md
├── docs/                   三份交接文档
├── frontend/               前端预留目录，目前只有占位文件
└── backend/
    ├── README.md           后端详细运行说明
    ├── requirements.txt    Python 依赖
    ├── app/                API、模型、权限及业务逻辑
    ├── scripts/seed.py     创建本地教师与学生测试账号
    ├── data/               本地 SQLite 数据库，不提交 Git
    └── tests/              测试文件已预留，尚未编写测试用例
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

- [健康检查](http://127.0.0.1:8000/health)
- [交互式接口文档](http://127.0.0.1:8000/docs)
- [OpenAPI 定义](http://127.0.0.1:8000/openapi.json)

后续日常启动只需运行最后一条 Uvicorn 命令。更多说明见 [后端 README](backend/README.md)。

## 当前限制与后续工作

- 尚未实现前端页面、积分账户与流水、奖励兑换。
- 当前未配置跨域；前端联调需要开发代理或由后端配置允许的前端来源。
- 没有注册、找回密码、文件上传、自动续期、服务端注销接口。
- 任务是共享的，没有班级隔离；所有教师都可审核待审核成果。
- 仅保存成果当前内容与反馈，没有完整修改历史、审核人和审核时间记录。
- 现有依赖尚未锁定版本；数据库结构变更尚未引入迁移工具。
- 业务在依赖安装完成后可本地运行，不调用外部 AI；但当前 `/docs` 的界面资源默认来自 CDN，不能承诺该页面断网仍可加载。离线演示前应准备本地前端及其资源并实测。
- `.env`、`.venv`、数据库文件不得提交 Git；默认只监听本机，不应直接作为公网生产服务部署。

## 验收状态

本轮已通过隔离数据库验收，覆盖登录、权限、提交、退回、重交、通过、防重复操作与输入校验。最终修正后另跑了 10 项接口复测及状态断言，均通过。

**这些是开发过程中的临时隔离测试，不代表仓库已经有可运行的自动化测试套件。** `backend/tests` 下的 Python 文件目前仍为空；补齐测试及落盘数据库重启验证由 C 同学牵头，前端端到端联调由 A/B/C 共同完成。

## 协作约定

- 接口字段和路径以 [后端交接文档](docs/backend-handoff.md) 与实际 OpenAPI 为准；修改前先同步调用方。
- A 主要修改前端；C 的积分实现复用现有登录和数据库连接，不另建第二套用户系统。
- `models.py`、`schemas.py`、`main.py`、`services/learning.py` 是共享修改点，修改前说明范围，避免互相覆盖。
- 教师审核通过与发积分必须使用同一个数据库事务；积分接入完成前，界面不能声称已经发放积分。
- 不通过删除现有数据库解决迁移问题；先备份、评估迁移，再测试。
