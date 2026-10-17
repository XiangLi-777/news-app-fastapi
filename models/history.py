from datetime import datetime
from sqlalchemy import Index, Integer, DateTime, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass


class History(Base):
    """浏览历史表"""
    __tablename__ = "history"

    __table_args__ = (
        # 同一个用户对同一个新闻只保留一条浏览记录，重复浏览时更新浏览时间
        UniqueConstraint("user_id", "news_id", name="user_news_history_unique"),
        Index("fk_history_user_idx", "user_id"),
        Index("fk_history_news_idx", "news_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="浏览记录ID")
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, comment="用户ID")
    news_id: Mapped[int] = mapped_column(Integer, nullable=False, comment="新闻ID")
    view_time: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now, comment="浏览时间")

    def __repr__(self):
        return f"<History(id={self.id}, user_id={self.user_id}, news_id={self.news_id}, view_time={self.view_time})>"
