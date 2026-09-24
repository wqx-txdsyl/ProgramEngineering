from getpass import getpass

from sqlmodel import Session, select

from app.database import create_db_and_tables, engine
from app.models import User
from app.services.auth import hash_password


def read_password(username: str) -> str:
    while True:
        password = getpass(
            f"请设置 {username} 的密码（8～128 个字符）："
        )

        if not 8 <= len(password) <= 128:
            print("密码长度不符合要求，请重新输入。")
            continue

        confirmation = getpass("请再次输入密码：")

        if password != confirmation:
            print("两次密码不一致，请重新输入。")
            continue

        return password


def main() -> None:
    create_db_and_tables()

    accounts = [
        ("teacher", "teacher"),
        ("student", "student"),
    ]

    with Session(engine) as session:
        for username, role in accounts:
            statement = select(User).where(
                User.username == username
            )
            existing_user = session.exec(statement).first()

            if existing_user is not None:
                print(f"{username} 已存在，跳过。")
                continue

            password = read_password(username)

            user = User(
                username=username,
                password_hash=hash_password(password),
                role=role,
            )

            session.add(user)
            session.commit()

            print(f"{username} 创建成功，身份：{role}")


if __name__ == "__main__":
    main()