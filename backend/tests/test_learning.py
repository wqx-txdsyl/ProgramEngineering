"""学习流程回归：提交查重、审核状态转换、归属检查（docs/data-points-tasks.md §7 第 2、4 项）。"""


def _submit(client, student, task_id: int, content: str = "我的成果") -> int:
    response = client.post(
        "/api/submissions",
        json={"task_id": task_id, "content": content},
        headers=student["headers"],
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


def test_教师创建任务_学生提交(client, make_user, make_task):
    teacher = make_user(role="teacher")
    student = make_user(role="student")
    task_id = make_task(teacher["headers"], "第一次任务")

    response = client.post(
        "/api/submissions",
        json={"task_id": task_id, "content": "我的成果"},
        headers=student["headers"],
    )

    assert response.status_code == 201
    assert response.json()["status"] == "pending"


def test_同一学生重复提交被拒_不同学生可提交同一任务(client, make_user, make_task):
    teacher = make_user(role="teacher")
    task_id = make_task(teacher["headers"])
    first_student = make_user(role="student")
    second_student = make_user(role="student")

    first = _submit(client, first_student, task_id, "第一份")

    duplicate = client.post(
        "/api/submissions",
        json={"task_id": task_id, "content": "再交一次"},
        headers=first_student["headers"],
    )
    assert duplicate.status_code == 409

    other = _submit(client, second_student, task_id, "第二个人的")
    assert other != first


def test_审核通过后再次审核返回409(client, make_user, make_task):
    teacher = make_user(role="teacher")
    student = make_user(role="student")
    task_id = make_task(teacher["headers"])
    submission_id = _submit(client, student, task_id)

    approved = client.post(
        f"/api/reviews/{submission_id}",
        json={"decision": "approved", "feedback": "好"},
        headers=teacher["headers"],
    )
    assert approved.status_code == 200
    assert approved.json()["status"] == "approved"

    again = client.post(
        f"/api/reviews/{submission_id}",
        json={"decision": "rejected", "feedback": "不行"},
        headers=teacher["headers"],
    )
    assert again.status_code == 409


def test_提交退回重交通过的完整流程(client, make_user, make_task):
    teacher = make_user(role="teacher")
    student = make_user(role="student")
    task_id = make_task(teacher["headers"])
    submission_id = _submit(client, student, task_id)

    rejected = client.post(
        f"/api/reviews/{submission_id}",
        json={"decision": "rejected", "feedback": "请补充说明"},
        headers=teacher["headers"],
    )
    assert rejected.status_code == 200
    assert rejected.json()["status"] == "rejected"

    resubmitted = client.put(
        f"/api/submissions/{submission_id}",
        json={"content": "改好了"},
        headers=student["headers"],
    )
    assert resubmitted.status_code == 200
    assert resubmitted.json()["status"] == "pending"
    assert resubmitted.json()["feedback"] == ""

    approved = client.post(
        f"/api/reviews/{submission_id}",
        json={"decision": "approved", "feedback": "通过"},
        headers=teacher["headers"],
    )
    assert approved.status_code == 200


def test_非法状态转换被拒绝(client, make_user, make_task):
    teacher = make_user(role="teacher")
    student = make_user(role="student")
    task_id = make_task(teacher["headers"])
    submission_id = _submit(client, student, task_id)

    # 待审核状态不能直接重交
    early_resubmit = client.put(
        f"/api/submissions/{submission_id}",
        json={"content": "还没退回就想改"},
        headers=student["headers"],
    )
    assert early_resubmit.status_code == 409


def test_已通过的成果不允许重交(client, make_user, make_task):
    teacher = make_user(role="teacher")
    student = make_user(role="student")
    task_id = make_task(teacher["headers"])
    submission_id = _submit(client, student, task_id)

    client.post(
        f"/api/reviews/{submission_id}",
        json={"decision": "approved", "feedback": "好"},
        headers=teacher["headers"],
    )

    response = client.put(
        f"/api/submissions/{submission_id}",
        json={"content": "通过之后还想改"},
        headers=student["headers"],
    )
    assert response.status_code == 409


def test_学生只能查看和修改自己的成果(client, make_user, make_task):
    teacher = make_user(role="teacher")
    task_id = make_task(teacher["headers"])
    owner = make_user(role="student")
    stranger = make_user(role="student")
    submission_id = _submit(client, owner, task_id)

    mine = client.get("/api/submissions/mine", headers=stranger["headers"])
    assert mine.status_code == 200
    assert all(row["student_id"] == stranger["id"] for row in mine.json())

    changed = client.put(
        f"/api/submissions/{submission_id}",
        json={"content": "想改别人的"},
        headers=stranger["headers"],
    )
    assert changed.status_code == 404
