from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from schemas.base import NewsItemBase

class HistoryRequest(BaseModel):
    """添加浏览记录"""
    news_id: int = Field(...,alias="newsId", description="新闻ID")


class HistoryNewsItemResponse(NewsItemBase):
    view_time: datetime = Field(...,alias="viewTime", description="浏览时间")
    model_config = ConfigDict(
        populate_by_name=True,  # 允许使用别名进行数据填充/字段名兼容
        from_attributes=True,  # 允许从ORM对象属性中填充数据
    )

class HistoryListResponse(BaseModel):
    """浏览历史列表"""
    list: list[HistoryNewsItemResponse]
    total: int
    has_more: bool = Field(...,alias="hasMore", description="是否有更多")
    model_config = ConfigDict(
        populate_by_name=True,  # 允许使用别名进行数据填充/字段名兼容
        from_attributes=True,  # 允许从ORM对象属性中填充数据
    )
