from datetime import datetime

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.history import History
from models.news import News
from models.users import User

async def add_news_history(
        news_id: int,
        user_id: int,
        db: AsyncSession,
    ):
    # 已浏览过时只更新浏览时间，避免触发唯一约束冲突(user_news_history_unique)
    query = select(History).where(History.user_id == user_id, History.news_id == news_id)
    existing = (await db.execute(query)).scalar_one_or_none()
    if existing:
        existing.view_time = datetime.now()
        await db.commit()
        await db.refresh(existing)
        return existing

    history=History(news_id=news_id,user_id=user_id)
    db.add(history)
    await db.commit()
    await db.refresh(history)
    return history

async def remove_news_history(
        news_id: int,
        user_id: int,
        db: AsyncSession,
    ):
    stmt=delete(History).where(History.user_id == user_id, History.news_id == news_id)
    result= await db.execute(stmt)
    await db.commit()
    return result.rowcount>0

async def get_history_list(
        db: AsyncSession,
        page: int,
        user_id: int,
        page_size: int=50
    ):
    # 获取浏览记录总量、获取浏览历史列表
    count_query=select(func.count()).where(History.user_id == user_id)
    count_result=await db.execute(count_query)
    total=count_result.scalar_one()

    # 获取浏览历史列表:连表查询（join）+分页+排序（浏览时间倒序）
    query=select(News,History.view_time.label("view_time")
                 ).join(History,History.news_id==News.id
                        ).where(History.user_id == user_id
                                ).order_by(History.view_time.desc()
                                           ).offset((page-1)*page_size).limit(page_size)
    # 结果是列表[(news,view_time)] 每个元组包含select里面的两项内容
    result=await db.execute(query)
    rows=result.all()
    return rows,total

# 清空当前用户浏览历史列表
async def remove_all_history(
        user_id: int,
        db: AsyncSession,
    ):
    stmt=delete(History).where(History.user_id == user_id)
    result= await db.execute(stmt)
    await db.commit()
    return result.rowcount or 0 # 返回删除的行数
