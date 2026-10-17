from fastapi import APIRouter,Depends, HTTPException,Query
from crud import news, news_cache
from config.db_conf import get_db
from sqlalchemy.ext.asyncio import AsyncSession


# 常见apirouter实例
# prefix 路由前缀（API 接口规范文档）
# tags 分组 标签
router=APIRouter(prefix="/api/news",tags=["news"])


# 基于上面的实例写装饰器
@router.get("/categories")
async def get_categories(
    skip:int=0,
    limit:int=100,
    db:AsyncSession=Depends(get_db)
):
    # 先获取数据库里面的新闻分类数据→先定义模型类→封装查询数据的方法 
    categories=await news_cache.get_categories(db,skip,limit)
    return {
        "code":200,
        "message":"获取新闻分类成功",
        "data":categories
    }

@router.get("/list")
async def get_news_list(
    category_id:int=Query(...,alias="categoryId",description="新闻分类id"), # 利用query参数获取参数，参数小写，用alias与前参数一致
    page:int=1,
    page_size:int=Query(...,alias="pageSize",le=100,description="每页数量"),
    db:AsyncSession=Depends(get_db)
):
    offset=(page-1)*page_size
    news_list=await news_cache.get_news_list(db,category_id,offset,page_size)
    total=await news.get_news_count(db,category_id)
    has_more=(offset+len(news_list))<total
    return {
        "code":200,
        "message":"获取新闻列表成功",
        "data":{
            "list":news_list,
            "total":total,
            "hasmore":has_more
        }
    }

@router.get("/detail")
async def get_news_detail(
    news_id:int=Query(...,alias="id",description="新闻id"),
    db:AsyncSession=Depends(get_db)
):
    news_detail=await news.get_news_detail(db,news_id)
    if not news_detail:
        raise HTTPException(status_code=404, detail="新闻不存在")
    views=await news.increase_news_views(db,news_detail.id)
    if not views:
        raise HTTPException(status_code=404, detail="增加浏览量失败")
    related_news=await news.get_related_news(db,news_detail.id,news_detail.category_id)
    return {
    "code": 200,
    "message": "success",
    "data": {
    "id": news_detail.id if news_detail else None,
    "title": news_detail.title if news_detail else None,
    "content": news_detail.content if news_detail else None,
    "image": news_detail.image if news_detail else None,
    "author": news_detail.author if news_detail else None,
    "publishTime": news_detail.publish_time if news_detail else None,
    "categoryId": news_detail.category_id if news_detail else None,
    "views": news_detail.views if news_detail else None,
    "relatedNews": related_news
  }
}

