from datetime import datetime, timedelta
import secrets
from fastapi import HTTPException
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from utils.security import get_hash_password,verify_password
from models.users import User, UserToken
from schemas.users import UserRequest, UserUpdateRequest
from cache.user_cache import delete_cached_token, get_cached_token_user_id, set_cached_token_user_id

# 根据用户名查询数据库
async def get_user(db: AsyncSession, username: str):
    query = select(User).where(User.username == username)
    result = await db.execute(query)
    return result.scalar_one_or_none()

# 创建用户
async def create_user(db: AsyncSession, user_data:UserRequest):
    # 先对密码加密处理→add
    hashed_password = get_hash_password(user_data.password)
    user = User(username=user_data.username, password=hashed_password)
    db.add(user)
    await db.commit()
    await db.refresh(user) # 刷新数据(从数据库中获取最新的user)
    return user

# 生成token
async def create_token(db: AsyncSession, user_id: int):
    # 创建token+设置过期时间+当前用户是否有权限（有更新，没有则添加）
    token = secrets.token_urlsafe(32)
    expire_time = datetime.now() + timedelta(days=7)
    query = select(UserToken).where(UserToken.user_id == user_id)
    result = await db.execute(query)
    user_token = result.scalar_one_or_none()

    if user_token: # 更新
        # 删除旧token的缓存，防止旧token在缓存有效期内仍可鉴权通过
        await delete_cached_token(user_token.token)
        user_token.token = token
        user_token.expires_at = expire_time

    else: # 添加
        user_token = UserToken(user_id=user_id, token=token, expires_at=expire_time)
        db.add(user_token)
    await db.commit()

    # 写入缓存：鉴权时先查缓存拿到user_id，避免每次请求都查user_token表
    await set_cached_token_user_id(token, user_id)
    return token


async def get_token(db: AsyncSession, token: str):
    # 先查缓存（高并发下鉴权请求大部分在这里命中，不打数据库）
    cached_user_id = await get_cached_token_user_id(token)
    if cached_user_id is not None:
        user = await db.get(User, cached_user_id)
        if user:
            return user
        # 缓存指向的用户已不存在（罕见情况）：删除缓存，走数据库兜底
        await delete_cached_token(token)

    query = select(UserToken).where(UserToken.token == token)
    result = await db.execute(query)
    db_token = result.scalar_one_or_none()
    if not db_token or db_token.expires_at < datetime.now(): # 过期
        return None
    query = select(User).where(User.id == db_token.user_id)
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    if user:
        # 回填缓存，加速后续请求
        await set_cached_token_user_id(token, user.id)
    return user


# 删除用户token（登出/修改密码时调用）：数据库记录+Redis缓存双清
async def delete_user_token(db: AsyncSession, token: str):
    # 删数据库记录
    await db.execute(delete(UserToken).where(UserToken.token == token))
    await db.commit()
    # 删缓存（必须双清，否则token在缓存过期前仍可通过鉴权）
    await delete_cached_token(token)

async def update_user(db: AsyncSession, username:str, user_data: UserUpdateRequest):
    # user_data是我们命名的pydantic对象，model_dump()方法将pydantic对象转换成字典(键值对)→**解包
    # 上传信息没有设置值的空值会被忽略，只更新有值的字段
    query=update(User).where(User.username == username).values(**user_data.model_dump(
        exclude_unset=True,
        exclude_none=True
    ))
    result = await db.execute(query)
    await db.commit()

    # 检查更新行数
    if result.rowcount == 0: # 没有更新
        raise HTTPException(status_code=404, detail="用户不存在")

    # 成功更新，通过用户名查询数据库
    update_user = await get_user(db, username)
    return update_user

# 修改密码:验证旧密码→更新新密码（新密码要记得加密处理）
async def change_password(db: AsyncSession, user:User, old_password: str, new_password: str):
    if not verify_password(old_password, user.password):
        return False
    hashed_new_pwd = get_hash_password(new_password)
    user.password = hashed_new_pwd
    db.add(user) # 这句是要理解的由sqlalchemy接管这个User对象,确保可以commit
    # 规避 session 是否过期或关闭导致不能提交的问题
    await db.commit()
    await db.refresh(user)
    return True


