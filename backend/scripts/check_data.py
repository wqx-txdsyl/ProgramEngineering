"""积分对账脚本（C 同学维护，docs/data-points-tasks.md §6、§8）。

演示或交付前运行：python -m scripts.check_data
检查余额与流水一致、兑换单与流水一致、库存与约束合法、奖励来源真实存在。
发现任何问题以非零退出码结束，全部通过打印"账实相符"。
"""
import sys

from sqlmodel import Session, select

from app.database import engine
from app.models import PointAccount, PointTransaction, Redemption, Reward, Submission
from app.services.points import (
    REDEMPTION_ACTIVE,
    REDEMPTION_CANCELLED,
    SOURCE_REDEEM,
    SOURCE_REFUND,
    SOURCE_REVIEW_APPROVED,
)


def main() -> int:
    problems: list[str] = []

    with Session(engine) as session:
        accounts = session.exec(select(PointAccount)).all()
        transactions = session.exec(select(PointTransaction)).all()
        redemptions = session.exec(select(Redemption)).all()
        rewards = session.exec(select(Reward)).all()
        submission_ids = {
            s.id for s in session.exec(select(Submission)).all()
            if s.status == "approved"
        }

        # 1. 账户余额必须等于该用户流水之和；流水存在但无账户也视为问题
        changes_by_user: dict[int, int] = {}
        for row in transactions:
            changes_by_user[row.user_id] = changes_by_user.get(row.user_id, 0) + row.change

        for account in accounts:
            expected = changes_by_user.get(account.user_id, 0)
            if account.balance != expected:
                problems.append(
                    f"[余额] 用户{account.user_id} 账户余额 {account.balance} != 流水和 {expected}"
                )
            if account.balance < 0:
                problems.append(f"[余额] 用户{account.user_id} 余额为负：{account.balance}")

        transaction_users = set(changes_by_user)
        account_users = {account.user_id for account in accounts}
        for user_id in transaction_users - account_users:
            problems.append(f"[账户] 用户{user_id} 有流水但无积分账户")

        # 2. 流水来源必须真实存在
        for row in transactions:
            if row.change == 0:
                problems.append(f"[流水] 流水{row.id} 变动为 0，无意义")
            if row.source_type == SOURCE_REVIEW_APPROVED and row.source_id not in submission_ids:
                problems.append(
                    f"[流水] 审核奖励流水{row.id} 指向不存在或未通过的成果{row.source_id}"
                )

        # 3. 兑换单一致性：有扣分流水；已取消的有退款流水；未取消的没有退款流水
        keys = {(t.user_id, t.source_type, t.source_id) for t in transactions}
        for red in redemptions:
            if (red.user_id, SOURCE_REDEEM, red.id) not in keys:
                problems.append(f"[兑换单] 兑换单{red.id} 缺少扣分流水")
            has_refund = (red.user_id, SOURCE_REFUND, red.id) in keys
            if red.status == REDEMPTION_CANCELLED and not has_refund:
                problems.append(f"[兑换单] 已取消单{red.id} 缺少退款流水")
            if red.status == REDEMPTION_ACTIVE and has_refund:
                problems.append(f"[兑换单] 未取消单{red.id} 却存在退款流水")
            if red.status not in (REDEMPTION_ACTIVE, REDEMPTION_CANCELLED):
                problems.append(f"[兑换单] 兑换单{red.id} 状态非法：{red.status}")

        # 4. 库存非负
        for reward in rewards:
            if reward.stock < 0:
                problems.append(f"[库存] 奖励{reward.id} {reward.name} 库存为负：{reward.stock}")

    if problems:
        print(f"❌ 发现 {len(problems)} 个问题：")
        for problem in problems:
            print("  " + problem)
        return 1

    print("✅ 账实相符：余额、流水、兑换单、库存全部通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
