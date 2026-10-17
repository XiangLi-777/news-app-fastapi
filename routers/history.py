from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from config.db_conf import get_db
from crud import history
from models.users import User
from schemas.history import HistoryListResponse, HistoryRequest
from utils.auth import get_current_user
from utils.response import success_response

router = APIRouter(prefix="/api/history", tags=["history"])

@router.post("/add")
async def add_history(data: HistoryRequest,
                         user:User = Depends(get_current_user),
                         db: AsyncSession = Depends(get_db)) :
    result=await history.add_news_history(data.news_id,user.id,db)
    return success_response(message="添加浏览记录成功",data=result)

@router.delete("/delete/{news_id}")
async def remove_history(news_id: int,
                         user:User = Depends(get_current_user),
                         db: AsyncSession = Depends(get_db)) :
    result=await history.remove_news_history(news_id,user.id,db)
    if not result:
        raise HTTPException(status_code=400, detail="删除浏览记录失败")
    return success_response(message="删除浏览记录成功")

@router.get("/list")
async def get_history_list(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(50, ge=1, le=100, alias="pageSize", description="每页数量"),
    user:User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)) :
    rows,total=await history.get_history_list(db,page,user.id,page_size)
    history_list=[
        {**news.__dict__,
        "view_time": view_time
        } for news,view_time in rows]
    has_more=total>page_size*page
    data=HistoryListResponse(list=history_list,total=total,has_more=has_more)
    return success_response(message="获取浏览历史列表成功",data=data)

@router.delete("/clear")
async def clear_history(user:User = Depends(get_current_user),
                         db: AsyncSession = Depends(get_db)) :
    result=await history.remove_all_history(user.id,db)
    return success_response(message=f"清空{result}条浏览记录成功")
