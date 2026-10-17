from uuid import uuid4
from pathlib import Path

from fastapi import APIRouter, Depends, Header, HTTPException, UploadFile, File
from models.users import User
from schemas.users import UserAuthResponse, UserChangePasswordRequest, UserInfoResponse, UserRequest, UserUpdateRequest
from config.db_conf import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from crud import users
from utils.auth import get_current_user
from utils.response import success_response
from utils.security import verify_password

router = APIRouter(prefix="/api/users", tags=["users"])

# 头像文件保存目录(与main.py中挂载的静态目录对应: /static/avatars/xxx.png)
AVATAR_DIR = Path(__file__).resolve().parent.parent / "uploads" / "avatars"
AVATAR_DIR.mkdir(parents=True, exist_ok=True)
# 允许的头像类型及对应扩展名
ALLOWED_AVATAR_TYPES = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/gif": "gif",
    "image/webp": "webp",
}
AVATAR_MAX_SIZE = 2 * 1024 * 1024  # 2MB

@router.post("/register")
async def register(user_data: UserRequest, db:AsyncSession = Depends(get_db)):
    existing_user = await users.get_user(db, user_data.username)
    if existing_user:
        raise HTTPException(status_code=400, detail="用户已存在")
    user = await users.create_user(db, user_data)
    token = await users.create_token(db, user.id)
    response_data = UserAuthResponse(token=token, user_info=UserInfoResponse.model_validate(user))
    return success_response(message="注册成功", data=response_data)

@router.post("/login")
async def login(user_data: UserRequest, db:AsyncSession = Depends(get_db)):
    user = await users.get_user(db, user_data.username)
    if not user or not verify_password(user_data.password, user.password): # 验证密码是否正确(明文密码与数据库中加密后的密码进行比对)
        raise HTTPException(status_code=400, detail="用户名或密码错误")
    token = await users.create_token(db, user.id)
    response_data = UserAuthResponse(token=token, user_info=UserInfoResponse.model_validate(user))
    return success_response(message="登录成功", data=response_data)

# 获取用户信息接口→封装CRUD→功能整合成一个工具函数→路由导入使用：注入依赖
@router.get("/info")
async def get_user_info(user = Depends(get_current_user)): # 此处没有db是因为不用调用数据库进行CRUD，仅仅要验证token拿到用户信息
    return success_response(message="获取用户信息成功", data=UserInfoResponse.model_validate(user))

# 修改用户信息接口:验证token→更新（用户输入数据put）→返回成功响应
@router.put("/update")
async def update_user_info(user_data: UserUpdateRequest, user = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    user=await users.update_user(db, user.username, user_data)
    return success_response(message="更新用户信息成功", data=UserInfoResponse.model_validate(user))

@router.put("/password")
async def update_user_password(
    password_data:UserChangePasswordRequest,
    authorization: str=Header(...,alias="Authorization"),
    user:User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    res_change_pwd=await users.change_password(db, user,password_data.old_password,password_data.new_password)
    if not res_change_pwd: # 旧密码错误
        raise HTTPException(status_code=400, detail="旧密码错误")
    # 修改密码后使token失效（数据库+缓存双清），强制用户重新登录
    token=authorization.split(" ")[1] # split按照空格分割去除前缀Bearer
    await users.delete_user_token(db, token)
    return success_response(message="修改密码成功")

# 登出接口:验证token→删除数据库token记录和Redis缓存(双清)→返回成功响应
@router.post("/logout")
async def logout(
    authorization: str=Header(...,alias="Authorization"),
    user:User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    token=authorization.split(" ")[1] # split按照空格分割去除前缀Bearer
    await users.delete_user_token(db, token)
    return success_response(message="登出成功")

# 修改头像接口:验证token→校验文件类型和大小→保存文件→更新用户avatar字段→返回头像路径
@router.post("/avatar")
async def update_user_avatar(
    avatar_file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    ext = ALLOWED_AVATAR_TYPES.get(avatar_file.content_type)
    if not ext:
        raise HTTPException(status_code=400, detail="仅支持 jpg/png/gif/webp 格式的头像")
    content = await avatar_file.read()
    if len(content) > AVATAR_MAX_SIZE:
        raise HTTPException(status_code=400, detail="头像图片大小不能超过2MB")
    # 文件名由服务端生成，避免使用用户上传的原始文件名(防路径穿越)
    filename = f"{user.id}_{uuid4().hex}.{ext}"
    (AVATAR_DIR / filename).write_bytes(content)
    avatar_path = f"/static/avatars/{filename}"
    user.avatar = avatar_path
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return success_response(message="头像更新成功", data={"avatar": avatar_path})
