from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
def success_response(data=None, message: str = "Success"):
    content = {
        "code": 200,
        "message": message,
        "data": data
    }
    # 返回成功的JSON响应(目标：任何的FastAPI、Pydantic、PRML对象都可以作为响应对象→code、message、data)
    return JSONResponse(content=jsonable_encoder(content))