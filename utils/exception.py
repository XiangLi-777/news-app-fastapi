import traceback
from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError,IntegrityError
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR

DEBUG_MODE = True # 是否开启调试模式，True 开启，False 关闭(开发模式，开发者可以看到详细的错误信息，生产模式下不建议开启)

async def http_exception_handler(request: Request, exc: HTTPException):
    """ 处理HTTPException异常 """
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": exc.status_code, "message": exc.detail, "data": None}
    )

async def integrity_error_handler(request: Request, exc: IntegrityError):
    """ 数据库完整性约束错误 """
    error_msg = str(exc.orig)
    # 判断具体的约束错误类型
    if "idx_user_username" in error_msg or "Duplicate entry" in error_msg:
        detail = "用户名已存在"
    elif "FOREIGN KEY" in error_msg:
        detail = "外键约束错误"
    else:
        detail = "数据库 integrity error(数据库约束冲突)"

    # 开发者模式下，返回详细的错误信息
    error_data=None
    if DEBUG_MODE:
        error_data = {
            "error_type": "integrity_error",
            "error_msg": error_msg,
            "path":str(request.url)
        }
    

    return JSONResponse(
        status_code=400,
        content={"code": 400, "message": detail, "data": error_data}
    )

async def validation_error_handler(request: Request, exc: RequestValidationError):
    """ 处理请求参数校验错误(如新密码长度不足) """
    # 去掉pydantic自定义校验器报错自带的 "Value error, " 前缀
    messages = [err.get("msg", "参数错误").replace("Value error, ", "") for err in exc.errors()]
    return JSONResponse(
        status_code=422,
        content={"code": 422, "message": "参数校验失败: " + "; ".join(messages), "data": None}
    )


async def sqlalchemy_error_handler(request: Request, exc: SQLAlchemyError):
    """ 处理SQLAlchemyError异常 """
    
    # 开发者模式下，返回详细的错误信息
    error_data=None
    if DEBUG_MODE:
        error_data = {
            "error_type": type(exc).__name__,
            "error_detail": str(exc),
            "traceback": traceback.format_exc(), # 格式化异常信息为字符串
            "path": str(request.url)
        }
    return JSONResponse(
        status_code=HTTP_500_INTERNAL_SERVER_ERROR,
        content={"code": 500, "message": "数据库错误", "data": error_data}
    )

async def general_exception_handler(request: Request, exc: Exception):
    """ 处理通用异常 """
    # 开发者模式下，返回详细的错误信息
    error_data=None
    if DEBUG_MODE:
        error_data = {
            "error_type": type(exc).__name__,
            "error_detail": str(exc),
            "traceback": traceback.format_exc(), # 格式化异常信息为字符串
            "path": str(request.url)
        }
    return JSONResponse(
        status_code=HTTP_500_INTERNAL_SERVER_ERROR,
        content={"code": 500, "message": "服务器内部错误", "data": error_data}
    )