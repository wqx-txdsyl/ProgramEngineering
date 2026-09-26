import itertools
from concurrent.futures import ThreadPoolExecutor

from fastapi import HTTPException
from sqlalchemy.exc import OperationalError
from sqlmodel import Session, SQLModel, create_engine, select, update

from app.models import (
    PointAccount,
    PointTransaction,
    Redemption,
    Reward,
    Submission,
    User,
)
from app.services.points import REVIEW_APPROVED_POINTS, redeem_reward


def _submit(client, student, task_id: int, content: str = "我的成果") -> int:
    response = client.post(
        "/api/submissions",
        json={"task_id": task_id, "content": content},
        headers=student["headers"],
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


def _review(client, teacher, submission_id: int, decision: str = "approved", feedback: str = "好"):
    return client.post(
        f"/api/reviews/{submission_id}",
        json={"decision": decision, "feedback": feedback},
        headers=teacher["headers"],
    )


def _balance(client, student) -> int:
    response = client.get("/api/points/me", headers=student["headers"])
    assert response.status_code == 200, response.text
    return response.json()["balance"]


def _transactions(client, student) -> list[dict]:
    response = client.get("/api/points/transactions", headers=student["headers"])
    assert response.status_code == 200
    return response.json()


def _add_reward(engine, **kwargs) -> int:
    with Session(engine) as session:
        reward = Reward(**kwargs)
        session.add(reward)
        session.commit()
        return reward.id


def _reward_stock(client, user, reward_id: int) -> int:
    rewards = client.get("/api/rewards", headers=user["headers"]).json()
    return next(r for r in rewards if r["id"] == reward_id)["stock"]



def test_审核通过恰好加一次分_重复审核不重复加分(client, make_user, make_task):
    teacher = make_user(role="teacher")
    student = make_user(role="student")
    task_id = make_task(teacher["headers"])
    submission_id = _submit(client, student, task_id)

    response = _review(client, teacher, submission_id)
    assert response.status_code == 200
    assert _balance(client, student) == REVIEW_APPROVED_POINTS

    second = _review(client, teacher, submission_id, decision="rejected", feedback="改")
    assert second.status_code == 409
    assert _balance(client, student) == REVIEW_APPROVED_POINTS

    rows = [t for t in _transactions(client, student) if t["source_type"] == "review_approved"]
    assert len(rows) == 1
    assert rows[0]["source_id"] == submission_id
    assert rows[0]["user_id"] == student["id"]


def test_积分按获益学生计入_不是按操作教师计入(client, make_user, make_task):
    teacher = make_user(role="teacher")
    student = make_user(role="student")
    task_id = make_task(teacher["headers"])
    submission_id = _submit(client, student, task_id)

    _review(client, teacher, submission_id)

    assert _balance(client, student) == REVIEW_APPROVED_POINTS
    teacher_points = client.get("/api/points/me", headers=teacher["headers"])
    assert teacher_points.status_code == 403


def test_退回与重交不加分_重交通过后也只加一次(client, make_user, make_task):
    teacher = make_user(role="teacher")
    student = make_user(role="student")
    task_id = make_task(teacher["headers"])
    submission_id = _submit(client, student, task_id)

    rejected = _review(client, teacher, submission_id, decision="rejected", feedback="补充说明")
    assert rejected.status_code == 200
    assert _balance(client, student) == 0

    resubmitted = client.put(
        f"/api/submissions/{submission_id}",
        json={"content": "改好了"},
        headers=student["headers"],
    )
    assert resubmitted.status_code == 200

    approved = _review(client, teacher, submission_id)
    assert approved.status_code == 200
    assert _balance(client, student) == REVIEW_APPROVED_POINTS

    rows = [t for t in _transactions(client, student) if t["source_type"] == "review_approved"]
    assert len(rows) == 1


def test_已有approved记录不会自动补发(client, make_user, make_task, engine):
    teacher = make_user(role="teacher")
    student = make_user(role="student")
    task_id = make_task(teacher["headers"])
    submission_id = _submit(client, student, task_id)

    with Session(engine) as session:
        session.execute(
            update(Submission)
            .where(Submission.id == submission_id)
            .values(status="approved")
        )
        session.commit()

    response = _review(client, teacher, submission_id)
    assert response.status_code == 409
    assert _balance(client, student) == 0


def test_积分写入失败时审核状态与余额都回滚(client, make_user, make_task, engine):
    teacher = make_user(role="teacher")
    student = make_user(role="student")
    task_id = make_task(teacher["headers"])
    submission_id = _submit(client, student, task_id)

    with Session(engine) as session:
        session.add(PointTransaction(
            user_id=student["id"],
            change=1,
            source_type="review_approved",
            source_id=submission_id,
        ))
        session.commit()

    response = _review(client, teacher, submission_id)
    assert response.status_code == 409

    with Session(engine) as session:
        assert session.get(Submission, submission_id).status == "pending"
        account = session.exec(
            select(PointAccount).where(PointAccount.user_id == student["id"])
        ).first()
        assert account is None or account.balance == 0


def test_学生只能看自己的积分流水_教师无积分接口(client, make_user, give_points):
    first = make_user(role="student")
    second = make_user(role="student")
    give_points(first["id"], 30)

    assert _balance(client, first) == 30
    assert _balance(client, second) == 0

    rows = _transactions(client, second)
    assert all(row["user_id"] == second["id"] for row in rows)

    teacher = make_user(role="teacher")
    assert client.get("/api/points/me", headers=teacher["headers"]).status_code == 403


def test_流水分页(client, make_user, give_points):
    student = make_user(role="student")
    give_points(student["id"], 5)
    give_points(student["id"], 6)
    give_points(student["id"], 7)

    page = client.get(
        "/api/points/transactions?offset=0&limit=2",
        headers=student["headers"],
    ).json()
    assert len(page) == 2
    assert {row["change"] for row in page} == {7, 6}



def test_兑换成功后余额库存流水兑换单一致(client, make_user, engine, give_points):
    student = make_user(role="student")
    give_points(student["id"], 50)
    reward_id = _add_reward(engine, name="专属徽章", cost=10, stock=3)

    response = client.post(
        f"/api/rewards/{reward_id}/redeem",
        json={"request_key": "rk-1"},
        headers=student["headers"],
    )
    assert response.status_code == 201, response.text
    redemption = response.json()
    assert redemption["status"] == "active"
    assert redemption["cost"] == 10

    assert _balance(client, student) == 40
    assert _reward_stock(client, student, reward_id) == 2

    redeem_rows = [
        t for t in _transactions(client, student) if t["source_type"] == "redeem"
    ]
    assert len(redeem_rows) == 1
    assert redeem_rows[0]["change"] == -10
    assert redeem_rows[0]["source_id"] == redemption["id"]

    mine = client.get("/api/rewards/redemptions/mine", headers=student["headers"]).json()
    assert [r["id"] for r in mine] == [redemption["id"]]


def test_重复请求幂等_同键换奖励被拒(client, make_user, engine, give_points):
    student = make_user(role="student")
    give_points(student["id"], 50)
    reward_id = _add_reward(engine, name="徽章", cost=10, stock=3)
    other_reward_id = _add_reward(engine, name="资料包", cost=15, stock=3)

    first = client.post(
        f"/api/rewards/{reward_id}/redeem",
        json={"request_key": "rk-1"},
        headers=student["headers"],
    )
    assert first.status_code == 201

    replay = client.post(
        f"/api/rewards/{reward_id}/redeem",
        json={"request_key": "rk-1"},
        headers=student["headers"],
    )
    assert replay.status_code == 200
    assert replay.json()["id"] == first.json()["id"]
    assert _balance(client, student) == 40
    assert _reward_stock(client, student, reward_id) == 2

    conflict = client.post(
        f"/api/rewards/{other_reward_id}/redeem",
        json={"request_key": "rk-1"},
        headers=student["headers"],
    )
    assert conflict.status_code == 409


def test_余额不足_库存为零_下架都不扣分(client, make_user, engine, give_points):
    poor = make_user(role="student")
    give_points(poor["id"], 5)
    rich = make_user(role="student")
    give_points(rich["id"], 100)

    costly = _add_reward(engine, name="很贵的", cost=50, stock=1)
    out_of_stock = _add_reward(engine, name="没货", cost=5, stock=0)
    offline = _add_reward(engine, name="已下架", cost=5, stock=5, is_active=False)

    assert client.post(
        f"/api/rewards/{costly}/redeem",
        json={"request_key": "k1"},
        headers=poor["headers"],
    ).status_code == 409
    assert client.post(
        f"/api/rewards/{out_of_stock}/redeem",
        json={"request_key": "k2"},
        headers=rich["headers"],
    ).status_code == 409
    assert client.post(
        f"/api/rewards/{offline}/redeem",
        json={"request_key": "k3"},
        headers=rich["headers"],
    ).status_code == 409

    assert _balance(client, poor) == 5
    assert _balance(client, rich) == 100
    assert [t for t in _transactions(client, poor) if t["source_type"] in ("redeem", "refund")] == []
    assert [t for t in _transactions(client, rich) if t["source_type"] in ("redeem", "refund")] == []


def test_取消只退一次_他人不能取消_库存恢复一次(client, make_user, engine, give_points):
    student = make_user(role="student")
    stranger = make_user(role="student")
    give_points(student["id"], 50)
    reward_id = _add_reward(engine, name="可退的", cost=10, stock=2)

    redemption_id = client.post(
        f"/api/rewards/{reward_id}/redeem",
        json={"request_key": "rk-1"},
        headers=student["headers"],
    ).json()["id"]

    cancel = client.post(
        f"/api/rewards/redemptions/{redemption_id}/cancel",
        headers=student["headers"],
    )
    assert cancel.status_code == 200
    assert cancel.json()["status"] == "cancelled"
    assert _balance(client, student) == 50

    again = client.post(
        f"/api/rewards/redemptions/{redemption_id}/cancel",
        headers=student["headers"],
    )
    assert again.status_code == 409
    assert _balance(client, student) == 50

    hijack = client.post(
        f"/api/rewards/redemptions/{redemption_id}/cancel",
        headers=stranger["headers"],
    )
    assert hijack.status_code == 404

    assert _reward_stock(client, student, reward_id) == 2
    refund_rows = [
        t for t in _transactions(client, student) if t["source_type"] == "refund"
    ]
    assert len(refund_rows) == 1



def test_并发兑换不透支不超卖(tmp_path):
    db_path = tmp_path / "concurrency.db"
    engine = create_engine(
        f"sqlite:///{db_path.as_posix()}",
        connect_args={"check_same_thread": False},
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        session.add(User(id=1, username="u1", password_hash="x", role="student"))
        session.add(User(id=2, username="u2", password_hash="x", role="student"))
        session.add(PointAccount(id=1, user_id=1, balance=100))
        session.add(PointAccount(id=2, user_id=2, balance=100))
        session.add(Reward(id=1, name="最后名额", cost=10, stock=1))
        session.commit()

    def attempt(user_id: int) -> str:
        try:
            with Session(engine) as session:
                redeem_reward(session, user_id, 1, f"req-{user_id}")
            return "ok"
        except HTTPException as error:
            return f"http-{error.status_code}"
        except OperationalError:
            return "busy"

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(attempt, [1, 2]))

    assert outcomes.count("ok") == 1
    with Session(engine) as session:
        assert session.get(Reward, 1).stock == 0
        deducts = session.exec(
            select(PointTransaction).where(PointTransaction.source_type == "redeem")
        ).all()
        assert len(deducts) == 1
        balances = {
            account.user_id: account.balance
            for account in session.exec(select(PointAccount)).all()
        }
        total_change = sum(
            transaction.change
            for transaction in session.exec(select(PointTransaction)).all()
        )
        assert balances[1] + balances[2] == 200 + total_change


def test_服务重启后状态仍在(tmp_path):
    db_path = tmp_path / "restart.db"
    url = f"sqlite:///{db_path.as_posix()}"
    engine_before = create_engine(url, connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine_before)
    with Session(engine_before) as session:
        session.add(User(id=1, username="u", password_hash="x", role="student"))
        session.add(Reward(id=1, name="徽章", cost=10, stock=5))
        session.commit()

    engine_after = create_engine(url, connect_args={"check_same_thread": False})
    with Session(engine_after) as session:
        from app.services.points import _apply_balance_change

        assert _apply_balance_change(session, 1, 30)
        session.add(PointTransaction(user_id=1, change=30, source_type="grant", source_id=1))
        session.commit()
        redeem_reward(session, 1, 1, "req-after-restart")

    with Session(engine_after) as session:
        account = session.exec(
            select(PointAccount).where(PointAccount.user_id == 1)
        ).one()
        assert account.balance == 20
        redemption = session.exec(select(Redemption)).one()
        assert redemption.status == "active"
        assert session.get(Reward, 1).stock == 4


def test_升级新增积分表不破坏原有数据(tmp_path):
    db_path = tmp_path / "upgrade.db"
    engine = create_engine(
        f"sqlite:///{db_path.as_posix()}",
        connect_args={"check_same_thread": False},
    )

    from sqlmodel import SQLModel as _SM

    legacy_tables = [
        table for table in _SM.metadata.sorted_tables
        if table.name in {"users", "tasks", "submissions"}
    ]
    _SM.metadata.create_all(engine, tables=legacy_tables)
    with Session(engine) as session:
        session.add(User(id=1, username="old_user", password_hash="x", role="student"))
        from app.models import Task

        session.add(Task(id=1, title="旧任务"))
        session.add(Submission(id=1, task_id=1, student_id=1, content="旧成果", status="approved"))
        session.commit()

    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        assert session.get(Submission, 1).content == "旧成果"
        assert session.get(User, 1).username == "old_user"
        from app.models import Task

        session.add(Reward(id=1, name="新奖励", cost=5, stock=1))
        session.commit()
        assert session.get(Reward, 1).stock == 1
