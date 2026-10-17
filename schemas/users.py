import re
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator



class UserRequest(BaseModel):
    username: str
    password: str

class UserInfoBase(BaseModel):
    """
    用户基础信息
    """
    nickname: Optional[str]=Field(None, max_length=50, description="昵称")
    avatar: Optional[str]=Field(None, max_length=255, description="头像")
    gender: Optional[str]=Field(None, max_length=10, description="性别")
    bio: Optional[str]=Field(None, max_length=500, description="个人简介")

class UserInfoResponse(UserInfoBase):
    id: int
    username: str

    # 模型封裝配置
    model_config = ConfigDict(
        from_attributes=True,  # 允许从ORM对象属性中填充数据
    )

# data要有自己的类型
class UserAuthResponse(BaseModel):
    token: str
    user_info: UserInfoResponse=Field(..., alias="userInfo")

    # 模型封裝配置
    model_config = ConfigDict(
        populate_by_name=True,  # 允许使用别名进行数据填充/字段名兼容
        from_attributes=True,  # 允许从ORM对象属性中填充数据
    )

# 更新用户信息的模型类
class UserUpdateRequest(UserInfoBase):
    nickname:str=None
    avatar:str=None
    gender:str=None
    bio:str=None
    phone:str=None

# 修改用户密码
class UserChangePasswordRequest(BaseModel):
    old_password: str=Field(..., alias="oldPassword", description="旧密码")
    new_password: str=Field(..., alias="newPassword", description="新密码(8-16位，且同时包含大写字母、小写字母和数字)")

    # 校验新密码强度: pydantic_core(Rust regex)不支持look-ahead(?=...)，因此拆成分步校验，
    # 规则等价于 ^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[A-Za-z0-9!@#$%^&*.]{8,16}$
    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str):
        if not re.fullmatch(r"[A-Za-z0-9!@#$%^&*.]{8,16}", v):
            raise ValueError("新密码需8-16位，且仅允许包含字母、数字和 !@#$%^&*. 字符")
        if not re.search(r"[a-z]", v) or not re.search(r"[A-Z]", v) or not re.search(r"\d", v):
            raise ValueError("新密码必须同时包含大写字母、小写字母和数字")
        return v
