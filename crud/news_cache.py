import asyncio

from fastapi.encoders import jsonable_encoder
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from cache.news_cache import (CATEGORIES_KEY, get_cached_categories, get_cached_news_list,
                              get_news_list_key, set_cached_categories, set_cached_news_list)
from config.cache_conf import acquire_lock, release_lock, set_cache
from models.news import Category, News

# 空结果缓存的过期时间：缓存空值防止穿透，过期时间要短，避免数据出现后长时间读不到
EMPTY_CACHE_EXPIRE=60
async def get_categories(
    db:AsyncSession,
    skip:int=0,
    limit:int=100
):
    # 先尝试从缓存中获取（用is not None判断：空列表也是有效缓存，防止穿透）
    cached_categories=await get_cached_categories()
    if cached_categories is not None:
        return cached_categories

    # 未命中时先抢互斥锁，防止热点key过期瞬间大量请求同时查库(缓存击穿)
    if not await acquire_lock(CATEGORIES_KEY):
        # 没抢到锁：等待持锁请求回填缓存后重读
        for _ in range(3):
            await asyncio.sleep(0.1)
            cached_categories=await get_cached_categories()
            if cached_categories is not None:
                return cached_categories
        # 重试后仍未命中(持锁请求可能失败)：兜底查库，不回填缓存
        stmt=select(Category).offset(skip).limit(limit)
        result=await db.execute(stmt)
        return jsonable_encoder(result.scalars().all())

    try:
        # 抢到锁后双重检查：等待锁期间其他请求可能已回填缓存
        cached_categories=await get_cached_categories()
        if cached_categories is not None:
            return cached_categories

        stmt=select(Category).offset(skip).limit(limit)
        result=await db.execute(stmt)
        categories=result.scalars().all()

        # 缓存中没有就查数据库，写入缓存，最终返回数据(旁路策略)
        # categories是ORM结果，需要转换成列表内部加字典
        categories=jsonable_encoder(categories)
        if categories:
            await set_cached_categories(categories)
        else:
            # 空结果也写入缓存(短过期)，防止穿透
            await set_cache(CATEGORIES_KEY,[],EMPTY_CACHE_EXPIRE)
        return categories
    finally:
        # 释放锁（持锁期间抛异常也能释放，锁自身也有10秒过期兜底）
        await release_lock(CATEGORIES_KEY)
    
    
async def get_news_list(
    db:AsyncSession,
    category_id:int,
    skip:int=0,
    limit:int=10,
):
    # 跳过的数量skip=（页码-1）*每页数量） → 页码=skip//limit+1
    page=skip//limit+1
    # 先尝试从缓存中获取（用is not None判断：空列表也是有效缓存，防止穿透）
    cached_news_list=await get_cached_news_list(category_id,page,limit)
    if cached_news_list is not None:  # 缓存中有数据
        return cached_news_list

    # 未命中时先抢互斥锁，防止热点key过期瞬间大量请求同时查库(缓存击穿)
    lock_key=get_news_list_key(category_id,page,limit)
    if not await acquire_lock(lock_key):
        # 没抢到锁：等待持锁请求回填缓存后重读
        for _ in range(3):
            await asyncio.sleep(0.1)
            cached_news_list=await get_cached_news_list(category_id,page,limit)
            if cached_news_list is not None:
                return cached_news_list
        # 重试后仍未命中(持锁请求可能失败)：兜底查库，不回填缓存
        stmt=select(News).where(News.category_id==category_id).offset(skip).limit(limit)
        result=await db.execute(stmt)
        return jsonable_encoder(result.scalars().all())

    try:
        # 抢到锁后双重检查：等待锁期间其他请求可能已回填缓存
        cached_news_list=await get_cached_news_list(category_id,page,limit)
        if cached_news_list is not None:
            return cached_news_list

        stmt=select(News).where(News.category_id==category_id).offset(skip).limit(limit)
        result=await db.execute(stmt)
        news_list=result.scalars().all()
        if news_list:  # 缓存中没有数据
            news_list=jsonable_encoder(news_list)
            await set_cached_news_list(category_id,page,limit,news_list)
        else:
            # 空结果也写入缓存(短过期)，防止穿透
            await set_cache(get_news_list_key(category_id,page,limit),[],EMPTY_CACHE_EXPIRE)
        return news_list
    finally:
        # 释放锁（持锁期间抛异常也能释放，锁自身也有10秒过期兜底）
        await release_lock(lock_key)

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