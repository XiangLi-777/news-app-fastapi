import json
from typing import Any

import redis.asyncio as redis   

REDIS_HOST = "localhost"

# 创建Redis的连接对象
redis_client=redis.Redis(
    host=REDIS_HOST,  # Redis服务器地址
    port=6379,  # Redis端口号
    db=0,  # 使用的Redis数据库索引
    decode_responses=True,  # 是否将响应解码为字符串
    protocol=2,  # 本机Redis为5.0，不支持HELLO命令(RESP3握手)，需显式用RESP2
)


# 设置缓存、读取缓存（字符串和列表或字典）

# 读取字符串
async def get_cache(key:str):
    # return await redis_client.get(key)
    try:
        return await redis_client.get(key)
    except Exception as e:
        print(f"获取缓存失败：{e}")
        return None

# 读取列表或字典
async def get_json_cache(key:str):
    try:
        data= await redis_client.get(key)
        if data: 
            return json.loads(data) # 序列化=Python 对象 → 字符串
    except Exception as e:
        print(f"获取缓存失败：{e}")
        return None 

# 设置缓存
async def set_cache(key:str,value:Any,expire:int=3600):
    try:
        if isinstance(value,dict) or isinstance(value,list): # 列表或字典
            value=json.dumps(value,ensure_ascii=False) # 字符串 → 序列化=Python对象
        await redis_client.setex(key, time=expire, value=value)
        return True

    except Exception as e:
        print(f"设置缓存失败：{e}")
        return None


# 尝试获取互斥锁（防缓存击穿）：SET key value NX EX，只有key不存在时才设置成功
# 抢到锁返回True；没抢到或Redis异常返回None（按未抢到处理）
# expire为锁的自动释放时间，防止持锁请求异常退出后锁永不释放
async def acquire_lock(key:str,expire:int=10):
    try:
        return await redis_client.set(f"lock:{key}","1",nx=True,ex=expire)
    except Exception as e:
        print(f"获取锁失败：{e}")
        return None

# 释放互斥锁
# 注意：若持锁时间超过expire，锁已自动过期并可能被其他请求抢走，此时delete会误删别人的锁
# 本项目持锁时间远小于expire，暂用简单delete；生产环境应使用Lua脚本比较锁值后删除
async def release_lock(key:str):
    try:
        await redis_client.delete(f"lock:{key}")
    except Exception as e:
        print(f"释放锁失败：{e}")


# 删除缓存
async def delete_cache(key:str):
    try:
        await redis_client.delete(key)
        return True
    except Exception as e:
        print(f"删除缓存失败：{e}")
        return None