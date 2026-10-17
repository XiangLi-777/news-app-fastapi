# 新闻相关的缓存方法
# key--value

import random
from typing import Any, Dict, List, Optional

from config.cache_conf import get_json_cache, set_cache


CATEGORIES_KEY="news:categories"
NEWS_LIST_PREFIX="news_list:"

# 获取新闻分类
async def get_cached_categories():
    return await get_json_cache(CATEGORIES_KEY)


# 写入新闻分类:缓存数据+过期时间
# 分类配置：7200；列表：600；详情：1800 验证码：120 -- 数据越稳定，缓存越持久
# 过期时间加随机抖动(0~300秒)，避免所有key同时过期引起缓存雪崩
async def set_cached_categories(data:List[Dict[str,Any]],expire:int=7200,jitter:bool=True):
   if jitter:
       expire=expire+random.randint(0,300)
   return await set_cache(CATEGORIES_KEY,data,expire)


# 生成新闻列表缓存的key：news_list:分类id:页码:每页数量
def get_news_list_key(category_id:Optional[int],page:int,size:int)->str:
    category_part=category_id if category_id is not None else "all"
    return f"{NEWS_LIST_PREFIX}{category_part}:{page}:{size}"


# 写入缓存 - 新闻列表 key=news_list:分类id：页码：每页数量  （+列表数据+过期时间）
# 过期时间加随机抖动，避免雪崩
async def set_cached_news_list(category_id:Optional[int],page:int,size:int,news_list:List[Dict[str,Any]],expire:int=1200,jitter:bool=True):
    if jitter:
        expire=expire+random.randint(0,300)
    key=get_news_list_key(category_id,page,size)
    await set_cache(key,news_list,expire)


# 读取缓存 - 新闻列表
async def get_cached_news_list(category_id:Optional[int],page:int,size:int):
    key=get_news_list_key(category_id,page,size)
    return await get_json_cache(key)