"""登录、身份与权限回归（docs/data-points-tasks.md §7 第 1 项）。"""


def test_登录成功并能查询身份(client, make_user):
    user = make_user(role="student")

    response = client.get("/api/auth/me", headers=user["headers"])

    assert response.status_code == 200
    assert response.json() == {
        "id": user["id"],
        "username": user["username"],
        "role": "student",
    }


def test_错误密码返回401(client, make_user):
    make_user(role="student", username="alice")

    response = client.post(
        "/api/auth/login",
        json={"username": "alice", "password": "wrong-password"},
    )

    assert response.status_code == 401


def test_不存在的用户返回401(client):
    response = client.post(
        "/api/auth/login",
        json={"username": "ghost", "password": "whatever123"},
    )

    assert response.status_code == 401


def test_无效Token返回401(client):
    response = client.get(
        "/api/auth/me",
        headers={"Authorization": "Bearer not-a-jwt"},
    )

    assert response.status_code == 401


def test_缺少Token返回401(client):
    assert client.get("/api/auth/me").status_code == 401


def test_学生不能创建任务(client, make_user):
    student = make_user(role="student")

    response = client.post(
        "/api/tasks",
        json={"title": "学生越权发布"},
        headers=student["headers"],
    )

    assert response.status_code == 403


def test_教师不能提交成果(client, make_user, make_task):
    teacher = make_user(role="teacher")
    task_id = make_task(teacher["headers"])

    response = client.post(
        "/api/submissions",
        json={"task_id": task_id, "content": "教师越权提交"},
        headers=teacher["headers"],
    )

    assert response.status_code == 403
