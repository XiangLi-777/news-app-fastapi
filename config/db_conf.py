import os

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import async_sessionmaker,AsyncSession,create_async_engine

# 加载.env文件中的环境变量(数据库连接信息不硬编码在代码里，避免泄露)
load_dotenv()

# 数据库URL：从环境变量读取连接信息(复制.env.example为.env并填入真实值)
ASYNC_DATABASE_URL = (
    f"mysql+asyncmy://{os.environ['DB_USER']}:{os.environ['DB_PASSWORD']}"
    f"@{os.environ['DB_HOST']}:{os.environ['DB_PORT']}/{os.environ['DB_NAME']}"
)

# 创建异步引擎
async_engine=create_async_engine(
    ASYNC_DATABASE_URL,
    echo=True,  # 输出SQL日志
    pool_size=10,
    max_overflow=20
)

# 创建异步会话工厂
AsyncSessionLocal=async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# 依赖项，用于数据库会话
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception: 
            await session.rollback()
            raise
        finally:
            await session.close()
