from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from models.news import Category, News
async def get_categories(
    db:AsyncSession,
    skip:int=0,
    limit:int=100
):
    stmt=select(Category).offset(skip).limit(limit)
    result=await db.execute(stmt)
    return result.scalars().all()
    
async def get_news_list(
    db:AsyncSession,
    category_id:int,
    skip:int=0,
    limit:int=10,
):
    stmt=select(News).where(News.category_id==category_id).offset(skip).limit(limit)
    result=await db.execute(stmt)
    return result.scalars().all()

async def get_news_count(
    db:AsyncSession,
    category_id:int
):
    stmt=select(func.count(News.id)).where(News.category_id==category_id)
    result=await db.execute(stmt)
    return result.scalar_one()

async def get_news_detail(
    db:AsyncSession,
    news_id:int
):
    stmt=select(News).where(News.id==news_id)
    result=await db.execute(stmt)
    return result.scalar_one_or_none()

async def increase_news_views(
    db:AsyncSession,
    news_id:int
):
    stmt=update(News).where(News.id==news_id).values(views=News.views+1)
    result=await db.execute(stmt)
    await db.commit()
    return result.rowcount>0

async def get_related_news(
    db:AsyncSession,
    news_id:int,
    category_id:int=None,
    limit:int=5
):
    stmt=select(News).where(News.id!=news_id)
    if category_id is not None:
        stmt=stmt.where(News.category_id==category_id)
    stmt=stmt.order_by(News.views.desc(),News.publish_time.desc()).limit(limit)
    result=await db.execute(stmt)
    related_news=result.scalars().all()
    # 列表推导式，推导出新闻的核心数据
    return [{
          "id": news_detail.id if news_detail else None,
          "title": news_detail.title if news_detail else None,
          "content": news_detail.content if news_detail else None,
          "image": news_detail.image if news_detail else None,
          "author": news_detail.author if news_detail else None,
          "publishTime": news_detail.publish_time if news_detail else None,
          "categoryId": news_detail.category_id if news_detail else None,
          "views": news_detail.views if news_detail else None,
        } for news_detail in related_news]