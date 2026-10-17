# 用户token相关的缓存方法
# key: token:{token值} → value: 用户id(纯字符串)
# 鉴权时先查缓存拿到user_id，再用主键查询用户，避免每次请求都查user_token表

from typing import Optional

from config.cache_conf import delete_cache, get_cache, set_cache


TOKEN_KEY_PREFIX="token:"
# token有效期7天(与crud/users.py中create_token的过期时间保持一致)
# 注意:token缓存不能加随机抖动，抖动会导致token已过期而缓存仍有效
TOKEN_EXPIRE=7*24*3600


# 生成token缓存的key
def get_token_key(token:str)->str:
    return f"{TOKEN_KEY_PREFIX}{token}"


# 读取token对应的用户id缓存
async def get_cached_token_user_id(token:str)->Optional[int]:
    user_id=await get_cache(get_token_key(token))
    return int(user_id) if user_id else None


# 写入token对应的用户id缓存
async def set_cached_token_user_id(token:str,user_id:int):
    return await set_cache(get_token_key(token),str(user_id),TOKEN_EXPIRE)


# 删除token缓存(登出/修改密码时调用，与数据库记录双清)
async def delete_cached_token(token:str):
    return await delete_cache(get_token_key(token))
