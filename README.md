# 简单图床

一个简单但够用的私有图床服务：

- 图片查看：公开访问
- 图片上传与管理：必须登录
- 标签管理：便于图片检索分类
- 支持前端压缩：减小空间和带宽压力
- 用户管理：仅 admin 可新增用户、修改用户密码，克制但亦可多人共用
- 零配置：命令行一键启动


### 体验地址

https://v.kingway.fun/simage/

用户：admin
密码：admin123456

> 体验地址数据定时删除，请勿放置重要数据


## 安装

```bash
pip install simple-image
```


## 启动

```bash
simple-image serve data_dir --host 0.0.0.0 --port 8000 --daemon
```

示例：

```bash
simple-image serve ./data \
  --api-url https://your.domain.com \
  --base-path /simple_image \
  --admin-username admin \
  --admin-password admin123456 \
  --compress-quality 25

# 使用 MySQL
simple-image serve ./data \
  --database-url mysql+pymysql://root:password@127.0.0.1:3306/simple_image \
  --api-url https://your.domain.com \
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
- `--daemon`: 守护进程后台运行

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

> 如部署到根目录，去除 simple_image 即可

先用子目录前缀启动服务：

```bash
simple-image serve ./data \
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
}
```

### 子路径部署建议

- 建议同时设置 `--base-path /simple_image` 与 `--api-url https://your.domain.com/simple_image`。
- 未显式设置 `SESSION_COOKIE_PATH` 时，程序会自动使用 `base_path` 作为 Cookie Path；你也可以手动指定。
- 若站点启用 HTTPS，建议设置 `SESSION_COOKIE_SECURE=true`。
- 如果图片更大或压缩耗时更高，按需增加 `client_max_body_size` 与 `proxy_read_timeout`。
- 发布后可先执行 `nginx -t`，再 `nginx -s reload`。



### 直接用 uvicorn 启动

```bash
uvicorn simple_image.main:app --host 0.0.0.0 --port 8000
```

### 默认管理员

首次启动时若不存在管理员用户，会自动创建：

- 用户名: `admin`
- 密码: `admin123456`

建议首次登录后立刻通过管理员功能修改密码。

### 重置管理员密码

忘记管理员密码时，可使用 `reset-admin-password` 命令重置：

```bash
simple-image reset-admin-password ./data
```

系统会自动查找唯一的 admin 用户并交互式输入新密码。如果存在多个管理员账号，需通过 `--username` 指定：

```bash
simple-image reset-admin-password ./data --username admin
```

使用 MySQL 等外部数据库时，同样支持 `--database-url`：

```bash
simple-image reset-admin-password ./data \
  --database-url mysql+pymysql://root:password@127.0.0.1:3306/simple_image
```

## 备份

只需备份 --data-dir 目录即可恢复或迁移整个服务。