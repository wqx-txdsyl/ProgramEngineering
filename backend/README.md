# 后端运行与维护说明

后端使用 Python 3.11 + FastAPI + SQLModel + SQLite。业务接口和字段详见 [后端交接文档](../docs/backend-handoff.md)，团队分工见 [项目 README](../README.md)。

## 1. 首次安装

以下命令都在项目的 `backend` 目录运行，使用 PowerShell。直接调用虚拟环境 Python，无需先激活环境。

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt --timeout 120
```

已有可用 `.venv` 时跳过创建。安装使用网络；下载超时可重试，不需要重建数据库。当前依赖文件未锁定版本，团队后续应记录已验证版本。

## 2. 配置本地密钥

```powershell
.\.venv\Scripts\python.exe -c "import secrets; print('JWT_SECRET_KEY=' + secrets.token_hex(32))"
```

把输出整行复制到本目录的 `.env` 文件；不要保存为 `.env.txt`。已有有效密钥则保留，不能每次启动都更换。当前 `config.py` 要求密钥至少 32 个字符，采用 HS256，Token 有效期 60 分钟。

不要把 `.env`、Token、真实密码写进共享文档或 Git。当前 `.env.example` 仍是空的，不是可直接使用的配置。

## 3. 创建本地测试账号

```powershell
.\.venv\Scripts\python.exe -m scripts.seed
```

脚本创建 `teacher`（教师）与 `student`（学生），分别提示设置 8～128 字符密码。输入不回显是正常情况。不存在统一默认密码；已有账号会跳过，不会重置密码。新成员应在自己的本地数据库初始化，不复制同学的真实数据库和密钥。

## 4. 启动与日常使用

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

- 默认地址：`http://127.0.0.1:8000`，只监听本机。
- [健康检查](http://127.0.0.1:8000/health) 应返回 `{"status":"ok"}`。
- [接口文档](http://127.0.0.1:8000/docs) 用于本机调试；[OpenAPI](http://127.0.0.1:8000/openapi.json) 用于确认实际接口。
- Ctrl+C 停止。修改代码会自动重载；修改 `.env` 后建议手动重启。
- 日常只需执行启动命令，不需要重复生成密钥和初始化账号。

Swagger 操作：先 POST 登录，复制返回的 `access_token`，点击 Authorize，只粘贴 Token，然后调用受保护接口。切换账号时先 Logout，再填新 Token。这里的 Logout 不会在服务器端撤销旧 Token。

默认 Swagger 界面依赖外部 CDN，完整离线演示前应准备并验证本地资源或本地前端，不能只凭 `/health` 成功就认为离线界面可用。

## 5. 数据和文件职责

数据库固定在本目录 `data/app.db`，由配置根据文件位置定位。启动建表会保留已有数据，但不负责迁移已有表结构。

| 文件/目录 | 职责 |
| --- | --- |
| `app/main.py` | 创建应用、启动建表、注册路由 |
| `app/config.py` | 数据库路径、JWT 配置 |
| `app/database.py` | 引擎、建表、数据库会话 |
| `app/models.py` | 数据库表结构 |
| `app/schemas.py` | 请求和响应格式 |
| `app/dependencies.py` | 登录和学生/教师权限检查 |
| `app/routers/` | HTTP 接口 |
| `app/services/` | 密码工具、审核与重交业务，积分文件仍预留 |
| `scripts/seed.py` | 初始化本地账号 |
| `tests/` | 自动化测试预留，目前 Python 文件为空 |

## 6. 联调与故障排查

- 401：确认是否已授权、Token 是否过期，以及是否更换了密钥。
- 403：账号角色不允许操作，不是服务器没启动。
- 409：重复提交或状态冲突，先刷新记录再判断，不盲目重试写请求。
- 422：检查字段名、空白内容、长度限制；审核请求使用 `decision`，不是 `status`。
- 500：查看运行 Uvicorn 的终端 traceback。若错误发生在保存后的响应阶段，记录可能已入库，先查询再重试。
- 找不到 `app`：确认终端位于 `backend`，使用上述模块启动命令。
- 前端浏览器报跨域：当前尚未配置 CORS；使用前端开发代理，或与后端确认精确允许的来源。
- 修改模型后表结构不变：`create_all()` 不是迁移工具，不要删除真实数据库，先商定迁移方案。

## 7. 测试状态与部署边界

基础流程已在临时隔离测试中验证，最终修正后 10 项接口复测通过。仓库测试文件仍为空，尚无完整持久化测试套件；C 同学需补齐测试依赖、用例和运行命令。

服务重启后的实际落盘数据、前端端到端、跨机器访问和并发积分兑换仍需专项验收。当前不具备完整公网部署所需的 HTTPS、登录限流、备份运维与令牌撤销机制，不要将开发模式直接开放公网。
