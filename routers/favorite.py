from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from config.db_conf import get_db
from crud import favorite
from crud.favorite import is_news_favorite,add_news_favorite
from models.users import User
from schemas.favorite import FavoriteCheckResponse, FavoriteListResponse, FavoriteRequest
from utils.auth import get_current_user
from utils.response import success_response

router = APIRouter(prefix="/api/favorite", tags=["favorite"])

@router.get("/check")
async def check_favorite(news_id: int=Query(...,alias="newsId" )
                         , user:User = Depends(get_current_user),
                         db: AsyncSession = Depends(get_db)) :
    is_favorited=await is_news_favorite(news_id,user,db)
    return success_response(message="获取收藏状态成功",data=FavoriteCheckResponse(isFavorite=is_favorited)) 

@router.post("/add")
async def add_favorite(data: FavoriteRequest, 
                         user:User = Depends(get_current_user),
                         db: AsyncSession = Depends(get_db)) :
    result=await add_news_favorite(data.news_id,user.id,db)
    return success_response(message="添加收藏成功",data=result)

@router.delete("/remove")
async def remove_favorite(news_id: int=Query(...,alias="newsId" )
                         , user:User = Depends(get_current_user),
                         db: AsyncSession = Depends(get_db)) :
    result=await favorite.remove_news_favorite(news_id,user.id,db)
    if not result: 
        raise HTTPException(status_code=400, detail="取消收藏失败")
    return success_response(message="取消收藏成功")

@router.get("/list")
async def get_favorite_list(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, alias="pageSize", description="每页数量"),
    user:User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)) :
    rows,total=await favorite.get_favorite_list(db,page,user.id,page_size)
    favorite_list=[
        {**news.__dict__,
        "favorite_id": favorite_id,
        "favorite_time": favorite_time
        } for news,favorite_id,favorite_time in rows]
    has_more=total>page_size*page
    data=FavoriteListResponse(list=favorite_list,total=total,has_more=has_more)
    return success_response(message="获取收藏列表成功",data=data)

@router.delete("/clear")
async def clear_favorite(user:User = Depends(get_current_user),
                         db: AsyncSession = Depends(get_db)) :
    result=await favorite.remove_all_favorite(user.id,db)
    return success_response(message=f"清空{result}条收藏成功")