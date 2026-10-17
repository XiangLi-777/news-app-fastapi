from passlib.context import CryptContext

# 创建密码上下文对象，指定使用的加密算法为 bcrypt，并设置过时的算法为自动处理  
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 密码加密
def get_hash_password(password: str):
    return pwd_context.hash(password)

# 密码校验
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)
# 拿数据库中的密码和用户输入的密码进行对比验证（用数据库里面密码的盐加明文密码再次加密比对）