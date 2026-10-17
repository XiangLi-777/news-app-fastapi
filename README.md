# 头条新闻 App 后端（news-app-fastapi）

一个新闻资讯类 App 的后端服务，基于 **FastAPI 异步框架 + MySQL + Redis** 实现，包含新闻浏览、用户认证、收藏、浏览历史四大功能模块，并针对高并发场景对缓存和鉴权做了专项优化。配套移动端前端为 Vue3 + Vant（H5）。

## 功能特性

- **新闻模块**：分类列表、分类新闻分页列表、新闻详情、相关推荐、浏览量统计
- **用户模块**：注册、登录、获取/修改资料、修改密码、头像上传、登出
- **收藏模块**：收藏/取消收藏/收藏状态/收藏列表/清空收藏（防重复收藏）
- **浏览历史**：记录/删除/历史列表/清空历史
- **缓存体系**：旁路缓存 + 防穿透（空值缓存）+ 防击穿（SETNX 互斥锁）+ 防雪崩（TTL 随机抖动）
- **认证体系**：bcrypt 密码加密 + 随机 token（MySQL 持久化 + Redis 加速），登出/改密码即时失效

## 技术栈

| 层面 | 技术 |
|---|---|
| Web 框架 | FastAPI + Pydantic v2（自动参数校验、OpenAPI 文档） |
| ORM | SQLAlchemy 2.0（async）+ asyncmy 异步驱动 |
| 数据库 | MySQL（连接池 pool_size=10 + max_overflow=20） |
| 缓存 | Redis（redis-py 异步客户端，RESP2 协议） |
| 认证 | passlib + bcrypt，随机字符串 token |
| 配置 | python-dotenv（.env 环境变量） |

## 目录结构

```
├── main.py               # 应用入口：注册路由、中间件、静态文件
├── config/               # 配置：数据库连接池、Redis 客户端
├── cache/                # 缓存 key 规范：新闻缓存、token 缓存
├── routers/              # 路由层：参数校验、依赖注入
├── crud/                 # 业务层：查缓存→查库→回填、事务
├── models/               # SQLAlchemy ORM 模型（含索引定义）
├── schemas/              # Pydantic 请求/响应模型
├── utils/                # 鉴权依赖、密码加密、统一响应、异常处理器
├── uploads/              # 用户上传文件（运行时创建，不入库）
├── .env.example          # 环境变量模板
└── requirements.txt      # 依赖清单
```

## 快速开始

### 环境要求

- Python 3.10+
- MySQL 5.7+（需先创建 `news_app` 数据库）
- Redis 5.0+（Windows 用户可用 tporadowski 移植版）

### 安装与配置

```bash
# 1. 克隆仓库
git clone https://github.com/XiangLi-777/news-app-fastapi.git
cd news-app-fastapi

# 2. 创建虚拟环境并安装依赖
python -m venv venv
venv\Scripts\activate        # Windows（Linux/macOS: source venv/bin/activate）
pip install -r requirements.txt

# 3. 配置环境变量
cp .env.example .env         # 编辑 .env，填入你的数据库连接信息

# 4. 创建数据库表（任选其一）
#    a) 用 Python 执行一次：
#       from models.users import Base; from config.db_conf import async_engine; ...
#       （models 各模块的 Base 可通过 SQLAlchemy metadata.create_all 建表）
#    b) 或按 models/ 中的模型定义手动建表：
#       user、user_token、news_category、news、favorite、history
```

### 启动

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

- 接口文档：http://127.0.0.1:8000/docs
- 健康检查：`GET /api/news/categories`

## API 摘要

| 模块 | 接口 | 说明 |
|---|---|---|
| 新闻 | `GET /api/news/categories` | 新闻分类（缓存 7200s） |
| 新闻 | `GET /api/news/list?categoryId=&page=&pageSize=` | 分类新闻分页列表（缓存 1200s，按需缓存） |
| 新闻 | `GET /api/news/detail?id=` | 新闻详情 + 相关推荐（浏览量 +1） |
| 用户 | `POST /api/users/register` / `POST /api/users/login` | 注册 / 登录，返回 token |
| 用户 | `GET /api/users/info` | 当前用户信息（Bearer token） |
| 用户 | `PUT /api/users/update` / `PUT /api/users/password` | 修改资料 / 修改密码 |
| 用户 | `POST /api/users/avatar` | 上传头像（jpg/png/gif/webp，≤2MB） |
| 用户 | `POST /api/users/logout` | 登出（token 双清） |
| 收藏 | `GET /api/favorite/check` `POST /api/favorite/add` `DELETE /api/favorite/remove` `GET /api/favorite/list` `DELETE /api/favorite/clear` | 收藏增删查 |
| 历史 | `POST /api/history/add` `DELETE /api/history/delete/{news_id}` `GET /api/history/list` `DELETE /api/history/clear` | 浏览历史 |

统一响应格式：`{"code": 200, "message": "...", "data": ...}`

## 缓存设计

**旁路缓存（Cache Aside）**：先查 Redis → 未命中查 MySQL → 回填 Redis。只有被访问过的数据才进缓存（按需缓存），冷门数据不占内存。

**过期时间分层**（数据越稳定缓存越久）：

| 数据 | key | TTL |
|---|---|---|
| 新闻分类 | `news:categories` | 7200s + 随机抖动 |
| 新闻列表 | `news_list:{分类id}:{页码}:{每页数量}` | 1200s + 随机抖动 |
| 空结果（防穿透） | 同上 | 60s |
| token | `token:{token值}` → user_id | 7 天 |

**防缓存三问题**：

- **穿透**：空结果也缓存 60s，命中判断用 `is not None` 而非 `if cached`（空列表也是有效缓存）
- **击穿**：SETNX 互斥锁（10s TTL 防死锁）+ 双重检查 + 抢锁失败等待重读 + 兜底查库
- **雪崩**：过期时间加 0~300s 随机抖动；Redis 建议配置 `maxmemory-policy volatile-lru` + `maxmemory`（本仓库缓存数据全部带 TTL，适合 volatile-lru）

## 认证设计

- **密码**：bcrypt 哈希存储（passlib），校验用同一盐重新哈希比对，明码不落库
- **密码强度**：8-16 位，必须同时包含大小写字母和数字（Pydantic validator 分步校验）
- **token 方案**：随机字符串（opaque token），MySQL `user_token` 表持久化 + Redis 缓存 `token → user_id`（7 天 TTL）
  - 鉴权时先查 Redis 拿 user_id，再主键查用户——**缓存命中时零 token 表查询**
  - 缓存只存 user_id，不存用户信息（个人信息和密码不进缓存）
- **失效机制**：登出/修改密码时数据库记录 + Redis 缓存**双清**，立即生效；修改密码后强制重新登录

## 注意事项

- 本仓库 Redis 客户端显式使用 RESP2 协议（`protocol=2`）：redis-py 8.x 默认 RESP3 握手，Redis 5.0 不支持 HELLO 命令；若你的 Redis ≥ 6.0，可去掉该参数
- `uploads/` 目录运行时自动创建（头像存储），已被 .gitignore 忽略
- 数据库连接信息通过 `.env` 配置，请勿将 `.env` 提交到仓库
