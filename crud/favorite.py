from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.favorite import Favorite
from models.news import News
from models.users import User

async def is_news_favorite(
        news_id: int,
        user: User,
        db: AsyncSession):
    query=select(Favorite).where(Favorite.user_id == user.id, Favorite.news_id == news_id)
    result=await db.execute(query)
    # 获取结果(是否有收藏记录，返回bool结果)
    return result.scalar_one_or_none() is not None

async def add_news_favorite(
        news_id: int,
        user_id: int,
        db: AsyncSession,
    ):
    # 已收藏时直接返回已有记录，避免触发唯一约束冲突(user_news_unique)
    query = select(Favorite).where(Favorite.user_id == user_id, Favorite.news_id == news_id)
    existing = (await db.execute(query)).scalar_one_or_none()
    if existing:
        return existing

    favorite=Favorite(news_id=news_id,user_id=user_id)
    db.add(favorite)
    await db.commit()
    await db.refresh(favorite)
    return favorite

async def remove_news_favorite(
        news_id: int,
        user_id: int,
        db: AsyncSession,
    ):
    stmt=delete(Favorite).where(Favorite.user_id == user_id, Favorite.news_id == news_id)
    result= await db.execute(stmt)
    await db.commit()
    return result.rowcount>0

async def get_favorite_list(
        db: AsyncSession,
        page: int,
        user_id: int,
         page_size: int=10
    ):
    # 获取收藏新闻总量、获取收藏新闻列表
    count_query=select(func.count()).where(Favorite.user_id == user_id)
    count_result=await db.execute(count_query)
    total=count_result.scalar_one()

    # 获取收藏新闻列表:连表查询（join）+分页+排序（收藏时间）
    # select(查询主体类型).join(联合查询模型类，联合查询的条件).where().order_by().offset().limit()
    # 连表查询相同字段可以在select里面通过label()指定别名
    query=select(News,Favorite.id.label("favorite_id"),Favorite.created_at.label("favorite_time")
                 ).join(Favorite,Favorite.news_id==News.id
                        ).where(Favorite.user_id == user_id
                                ).order_by(Favorite.created_at.desc()
                                           ).offset((page-1)*page_size).limit(page_size)
    # 结果是列表[(news,favorite_id,favorite_time)] 每个元组包含select里面的三项内容
    result=await db.execute(query)
    rows=result.all()
    return rows,total

# 清空当前用户收藏列表
async def remove_all_favorite(
        user_id: int,
        db: AsyncSession,
    ):
    stmt=delete(Favorite).where(Favorite.user_id == user_id)
    result= await db.execute(stmt)
    await db.commit()
    return result.rowcount or 0 # 返回删除的行数



   