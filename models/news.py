from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, Index
from sqlalchemy.orm import DeclarativeBase,Mapped,mapped_column

class Base(DeclarativeBase):
    created_at:Mapped[datetime]=mapped_column(
        DateTime,
        default=datetime.now(),
        comment="创建时间"
    )

    updated_at:Mapped[datetime]=mapped_column(
        DateTime,
        default=datetime.now(),
        onupdate=datetime.now(),
        comment="更新时间"
    )

class Category(Base):
    __tablename__="news_category"

    id:Mapped[int]=mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="分类id"
    )

    name:Mapped[str]=mapped_column(
        String(50),
        unique=True,
        nullable=False,
        comment="分类名称"
    )

    sort_order:Mapped[int]=mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="排序"
    )

    def __repr__(self):
        return f"<Category(id={self.id}, name={self.name},sort_order={self.sort_order})>"


from sqlalchemy import Integer, String, Text, Index

class News(Base):
    __tablename__ = "news"

    # 使用 __table_args__ 配置索引，category_id、publish_time 两个单列索引
    __table_args__ = (
        Index("fk_news_category_idx", "category_id"),
        Index("idx_news_publish_time", "publish_time"),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="新闻id"
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="新闻标题"
    )

    description: Mapped[str] = mapped_column(
        String(500),
        nullable=True,
        comment="新闻简介"
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=True,
        comment="新闻内容"
    )

    image: Mapped[str] = mapped_column(
        String(255),
        nullable=True,
        comment="新闻图片地址"
    )

    author: Mapped[str] = mapped_column(
        String(50),
        nullable=True,
        comment="作者"
    )

    category_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="分类id"
    )

    views: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="浏览量"
    )

    publish_time: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        comment="发布时间"
    )

    def __repr__(self):
        return f"<News(id={self.id}, title={self.title}, category_id={self.category_id})>"