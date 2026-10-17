from sqlalchemy.exc import SQLAlchemyError,IntegrityError

from fastapi import HTTPException
from fastapi.exceptions import RequestValidationError

from utils.exception import http_exception_handler, integrity_error_handler, sqlalchemy_error_handler, general_exception_handler, validation_error_handler


def register_exception_handlers(app):
    """
    注册异常处理函数:子类继承HTTPException，则优先处理（子类在前，父类在后）
    :param app: FastAPI实例
    """
    app.add_exception_handler(HTTPException, http_exception_handler) # 业务层面的报错
    app.add_exception_handler(RequestValidationError, validation_error_handler) # 请求参数校验错误
    app.add_exception_handler(IntegrityError, integrity_error_handler) # 数据库完整性约束错误
    app.add_exception_handler(SQLAlchemyError, sqlalchemy_error_handler) # 数据库操作错误
    app.add_exception_handler(Exception, general_exception_handler) # 通用异常处理
    