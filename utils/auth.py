from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends, HTTPException, Header
from crud import users
from config.db_conf import get_db

# 整合、根据Token查询用户信息并返回
# get_token内部会先查Redis缓存(token→user_id)，未命中再查数据库并回填缓存
async def get_current_user(authorization: str=Header(...,alias="Authorization"),
                           db: AsyncSession = Depends(get_db)
):
    token=authorization.split(" ")[1] # split是按照空格进行分割得到列表，去除前缀Bearer
    user = await users.get_token(db,token)
    if not user:
        raise HTTPException(status_code=401, detail="无效令牌或令牌已过期")
    return user
