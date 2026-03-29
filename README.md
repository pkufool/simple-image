# simple-image

一个可发布到 PyPI 的简单图床包：

- 后端：FastAPI + SQLAlchemy（支持 SQLite / MySQL）
- 前端：Vue3 + Element Plus（由 FastAPI 静态托管）
- 图片查看：公开访问
- 图片上传与管理：必须登录
- 登录会话：HttpOnly Cookie 承载（不再使用 localStorage token）
- 用户管理：仅 admin 可新增用户、修改用户密码
- 上传压缩策略：admin 可针对每个用户设置“是否压缩”与“压缩率”

## 安装

开发环境：

```bash
pip install -r requirements.txt
```

打包安装（本地）：

```bash
pip install .
```

## 命令行启动

安装后可直接使用：

```bash
simple-image serve data_dir --host 0.0.0.0 --port 8000 --reload
```

示例：

```bash
simple-image serve ./runtime-data \
  --api-url http://localhost:8000 \
  --admin-username admin \
  --admin-password admin123456 \
  --compress-quality 25

# 使用 MySQL
simple-image serve ./runtime-data \
  --database-url mysql+pymysql://root:password@127.0.0.1:3306/simple_image \
  --api-url http://localhost:8000
```

参数说明：

- `data_dir`: 运行数据目录（数据库和图片文件）
- `--host`: 监听地址（默认 `0.0.0.0`）
- `--port`: 监听端口（默认 `8000`）
- `--reload`: 自动重载（开发模式）
- `--api-url`: 对外展示的图片 URL 前缀
- `--admin-username`: 启动时自动创建管理员用户名
- `--admin-password`: 启动时自动创建管理员密码
- `--database-url`: 数据库连接串（未设置时默认使用 `data_dir/database.db`）
- `--compress-quality`: 默认压缩质量（1-95）

也可通过环境变量配置数据库：

- `SIMPLE_IMAGE_DATABASE_URL`
- `DATABASE_URL`（兼容通用部署环境）

会话 Cookie 相关环境变量：

- `SESSION_COOKIE_SECURE`：是否仅 HTTPS 传输（生产建议 `true`）
- `SESSION_COOKIE_SAMESITE`：默认 `lax`
- `SESSION_COOKIE_DOMAIN`：可选
- `SESSION_COOKIE_PATH`：默认 `/`
- `SESSION_MAX_AGE`：默认 `604800`（7 天）

## 直接用 uvicorn 启动

```bash
uvicorn simple_image.main:app --host 0.0.0.0 --port 8000
```

## 浏览器访问

- 首页: http://localhost:8000/
- API 文档: http://localhost:8000/docs

## 默认管理员

首次启动时若不存在管理员用户，会自动创建：

- 用户名: `admin`
- 密码: `admin123456`

建议首次登录后立刻通过管理员功能修改密码。

## 目录

- `simple_image/`: Python 包与前端静态资源
- `data/`: 运行数据（默认）
- `pyproject.toml`: PyPI 打包配置
