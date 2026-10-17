from datetime import datetime
from sqlalchemy import ForeignKey, Integer, String, Enum, TIMESTAMP, Index
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class User(Base):
    """用户表"""
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False, comment="用户ID")
    username: Mapped[str] = mapped_column(String(50), nullable=False, comment="用户名")
    password: Mapped[str] = mapped_column(String(255), nullable=False, comment="密码(加密存储)")
    nickname: Mapped[str | None] = mapped_column(String(50), nullable=True, comment="昵称")
    avatar: Mapped[str | None] = mapped_column(String(255), nullable=True, comment="头像URL")
    gender: Mapped[str | None] = mapped_column(Enum("男", "女", "未知"), nullable=True, comment="性别")
    bio: Mapped[str | None] = mapped_column(String(500), nullable=True, comment="个人简介")
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True, comment="手机号")
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False, default=datetime.now, comment="创建时间")
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False, default=datetime.now, onupdate=datetime.now, comment="更新时间")

    # 使用 __table_args__ 创建索引：username普通索引，phone普通索引
    __table_args__ = (
        Index("idx_user_username", "username"),
        Index("idx_user_phone", "phone"),
    )

    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, nickname={self.nickname}, avatar={self.avatar}, gender={self.gender}, bio={self.bio}, phone={self.phone}, created_at={self.created_at}, updated_at={self.updated_at})>"

class UserToken(Base):
    __tablename__ = "user_token"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, nullable=False, comment="令牌ID")
    user_id: Mapped[int] = mapped_column(Integer,ForeignKey(User.id), nullable=False, comment="用户ID")
    token: Mapped[str] = mapped_column(String(255), nullable=False, comment="令牌值")
    expires_at: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False, comment="过期时间")
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False, default=datetime.now, comment="创建时间")