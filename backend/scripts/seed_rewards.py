"""奖励演示数据初始化（C 同学维护，docs/data-points-tasks.md §3、§5）。

可重复运行：按固定 id 插入，已存在的奖励跳过，不修改、不删除、不重置。
用法：python -m scripts.seed_rewards
"""
from sqlmodel import Session

from app.database import create_db_and_tables, engine
from app.models import Reward

# 全部标注"演示"；AI 额度等无真实供应方的条目在描述里明确说明
DEMO_REWARDS = [
    {
        "id": 1,
        "name": "专属成就徽章（演示）",
        "description": "个人主页展示的电子徽章",
        "cost": 10,
        "stock": 20,
        "is_active": True,
    },
    {
        "id": 2,
        "name": "拓展学习资料包（演示）",
        "description": "指定学习资料的下载权限",
        "cost": 15,
        "stock": 10,
        "is_active": True,
    },
    {
        "id": 3,
        "name": "AI 分步提示额度（演示）",
        "description": "站内 AI 分步提示 5 次；当前无真实供应方，仅演示兑换流程",
        "cost": 20,
        "stock": 5,
        "is_active": True,
    },
    {
        "id": 4,
        "name": "已下架示例：过期讲座门票",
        "description": "演示'不可兑换'状态的条目，不会出现在奖励列表",
        "cost": 8,
        "stock": 0,
        "is_active": False,
    },
]


def main() -> None:
    create_db_and_tables()

    with Session(engine) as session:
        for spec in DEMO_REWARDS:
            existing = session.get(Reward, spec["id"])

            if existing is not None:
                print(f"奖励 {spec['id']} 已存在，跳过：{existing.name}")
                continue

            session.add(Reward(**spec))
            session.commit()
            print(f"奖励已创建：{spec['name']}（{spec['cost']} 分，库存 {spec['stock']}）")

    print("✅ 奖励演示数据就绪（可重复执行，已存在的不会改动）")


if __name__ == "__main__":
    main()
