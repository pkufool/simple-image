# simple-image

一个可发布到 PyPI 的简单图床包：

- 后端：FastAPI + SQLAlchemy（支持 SQLite / MySQL）
- 前端：Vue3 + Element Plus（由 FastAPI 静态托管）
- 图片查看：公开访问
- 图片上传与管理：必须登录
- 登录会话：HttpOnly Cookie 承载
- 用户管理：仅 admin 可新增用户、修改用户密码
- 上传压缩策略：admin 可针对每个用户设置“是否压缩”与“压缩率”
- iPhone 图片兼容：支持 HEIC/HEIF 上传（服务端自动转 JPEG 存储），并自动处理 EXIF 方向

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
  --base-path /simple_image \
  --admin-username admin \
  --admin-password admin123456 \
  --compress-quality 25

# 使用 MySQL
simple-image serve ./runtime-data \
  --database-url mysql+pymysql://root:password@127.0.0.1:3306/simple_image \
  --api-url http://localhost:8000 \
  --base-path /simple_image
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
- `--base-path`: 子目录部署前缀，例如 `/simple_image`

也可通过环境变量配置数据库：

- `SIMPLE_IMAGE_DATABASE_URL`
- `DATABASE_URL`（兼容通用部署环境）

也可通过环境变量配置子目录部署前缀：

- `SIMPLE_IMAGE_BASE_PATH`
- `BASE_PATH`（兼容通用部署环境）

会话 Cookie 相关环境变量：

- `SESSION_COOKIE_SECURE`：是否仅 HTTPS 传输（生产建议 `true`）
- `SESSION_COOKIE_SAMESITE`：默认 `lax`
- `SESSION_COOKIE_DOMAIN`：可选
- `SESSION_COOKIE_PATH`：默认 `/`
- `SESSION_MAX_AGE`：默认 `604800`（7 天）

## Nginx 反向代理（部署到 /simple_image）

先用子目录前缀启动服务：

```bash
simple-image serve ./runtime-data \
  --host 127.0.0.1 \
  --port 8000 \
  --base-path /simple_image \
  --api-url https://your.domain.com/simple_image
```

然后用 Nginx 转发（保留原始 URI，不去掉 `/simple_image` 前缀）：

```nginx
upstream simple_image_backend {
  server 127.0.0.1:8000;
  keepalive 32;
}

server {
  listen 80;
  server_name your.domain.com;

  # 统一到带尾斜杠的入口，保证相对静态资源路径稳定
  location = /simple_image {
    return 301 /simple_image/;
  }

  # API + 前端入口（保留 /simple_image 前缀）
  location /simple_image/ {
    proxy_pass http://simple_image_backend;
    proxy_http_version 1.1;

    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;

    client_max_body_size 20m;
    proxy_read_timeout 300s;
    proxy_send_timeout 300s;

    # HTML 与 API 响应不建议长期缓存
    expires -1;
    add_header Cache-Control "no-store";
  }

  # gzip（对文本类资源压缩，对图片无需重复压缩）
  gzip on;
  gzip_comp_level 5;
  gzip_min_length 1024;
  gzip_vary on;
  gzip_proxied any;
  gzip_types
    text/plain
    text/css
    text/javascript
    application/javascript
    application/json
    application/xml
    image/svg+xml;
}
```

### 子路径部署建议

- 建议同时设置 `--base-path /simple_image` 与 `--api-url https://your.domain.com/simple_image`。
- 未显式设置 `SESSION_COOKIE_PATH` 时，程序会自动使用 `base_path` 作为 Cookie Path；你也可以手动指定。
- 若站点启用 HTTPS，建议设置 `SESSION_COOKIE_SECURE=true`。
- 如果图片更大或压缩耗时更高，按需增加 `client_max_body_size` 与 `proxy_read_timeout`。
- 发布后可先执行 `nginx -t`，再 `nginx -s reload`。

如果你的 Nginx 必须使用“去前缀转发”（例如 `proxy_pass http://backend/;`），可不使用 `--base-path`，改为继续设置：

- `proxy_set_header X-Forwarded-Prefix /simple_image`
- `SESSION_COOKIE_PATH=/simple_image`

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
