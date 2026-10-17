from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from routers import favorite, history, news, users
from fastapi.middleware.cors import CORSMiddleware
from utils.exception_handlers import register_exception_handlers

app=FastAPI()
register_exception_handlers(app) # 注册异常处理器

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # 允许的源，上线时改成实际部署的源
    allow_credentials=True, # 允许的凭证
    allow_methods=["*"], # 允许的请求方法
    allow_headers=["*"], # 允许的请求头
)

# 挂载静态文件目录(头像等上传文件)，与routers/users.py中AVATAR_DIR对应
UPLOAD_DIR = Path(__file__).parent / "uploads"
(UPLOAD_DIR / "avatars").mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(UPLOAD_DIR)), name="static")


# 挂载路由/注册路由
app.include_router(news.router)
app.include_router(users.router)
app.include_router(favorite.router)
app.include_router(history.router)