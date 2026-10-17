from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from schemas.base import NewsItemBase

class FavoriteCheckResponse(BaseModel):
    """判断是否已收藏"""
    is_favorite: bool = Field(...,alias="isFavorite", description="是否已收藏")


class FavoriteRequest(BaseModel):
    """添加收藏"""
    news_id: int = Field(...,alias="newsId", description="新闻ID")


# 规划两个类：一个新闻模型类，一个收藏列表模型类
class FavoriteNewsItemResponse(NewsItemBase):
    favorite_id: int = Field(...,alias="favoriteId", description="收藏ID")
    favorite_time: datetime = Field(...,alias="favoriteTime", description="收藏时间")
    model_config = ConfigDict(
        populate_by_name=True,  # 允许使用别名进行数据填充/字段名兼容
        from_attributes=True,  # 允许从ORM对象属性中填充数据
    )

class FavoriteListResponse(BaseModel):
    """收藏列表"""
    list: list[FavoriteNewsItemResponse]
    total: int
    has_more: bool = Field(...,alias="hasMore", description="是否有更多")
    model_config = ConfigDict(
        populate_by_name=True,  # 允许使用别名进行数据填充/字段名兼容
        from_attributes=True,  # 允许从ORM对象属性中填充数据
    )