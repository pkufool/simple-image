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

> 名字太像也不让 publish 😑

```bash
pip install simple-image-hosting
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
- `--api-url`: 对外展示的图片和缩略图 URL 前缀；管理 API 与下载仍使用当前站点地址
- `--admin-username`: 仅在管理员不存在时用于首次创建
- `--admin-password`: 仅在管理员不存在时用于首次创建，不会在重启时覆盖现有密码
- `--database-url`: 数据库连接串（未设置时默认使用 `data_dir/database.db`）
- `--compress-quality`: 默认压缩质量（1-95）
- `--base-path`: 子目录部署前缀，例如 `/simple_image`
- `--allowed-image-domain`: 允许加载图片的来源域名，可重复指定并支持 `*.example.com`
- `--daemon`: 守护进程后台运行

也可通过环境变量配置数据库：

- `SIMPLE_IMAGE_DATABASE_URL`
- `DATABASE_URL`（兼容通用部署环境）

### SQLite 性能与部署建议

使用默认的本地 SQLite 数据库时，服务会自动启用以下配置：

- WAL 日志模式，允许读取请求与写入请求并行执行
- `synchronous=NORMAL`，在性能与可靠性之间取平衡
- 30 秒锁等待，降低短时并发写入时出现 `database is locked` 的概率
- 自动 WAL checkpoint，并将 checkpoint 后 WAL 文件的保留上限设置为 64 MiB
- 每个进程最多 10 个数据库连接（5 个常驻连接 + 5 个临时连接）

WAL 仍然只允许同一时间有一个写入者。SQLite 应存放在本机磁盘，并建议保持单个应用进程；如需多个 worker、多台主机或持续高并发写入，请使用 MySQL。不要把 WAL 数据库放在 NFS 等普通网络文件系统上。

### 图片来源域名限制（可选）

默认不限制来源，任何域名都可以展示公开图片。要限制 `/image/*` 和 `/thumbnail/*`，可重复指定允许的域名：

```bash
simple-image serve ./data \
  --allowed-image-domain www.example.com \
  --allowed-image-domain '*.trusted.example.com'
```

也可以使用逗号分隔的环境变量：

```bash
SIMPLE_IMAGE_ALLOWED_DOMAINS='www.example.com,*.trusted.example.com'
```

精确规则只匹配该域名；`*.example.com` 匹配其一级或多级子域名，但不匹配 `example.com` 本身。如两者都需要，请同时配置。域名不区分大小写。

启用后采用严格模式：浏览器请求的 `Origin`（存在时优先）或 `Referer` 必须匹配规则。没有这两个请求头的地址栏直开、`curl`、隐藏 Referer 的页面以及部分隐私客户端会收到 403。Nginx 默认会转发这两个请求头，请勿主动清除。

限制模式会将图片响应设置为 `private, no-store`，避免共享缓存绕过检查。启用前应清理 CDN、代理和浏览器中已有的公开图片缓存，并确保代理/CDN 不覆盖应用返回的缓存头。

这项功能用于减少普通盗链和带宽滥用，不是私有访问控制；非浏览器客户端可以伪造 `Origin` 或 `Referer`。敏感图片应使用认证下载或签名 URL。

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
uvicorn simple_image.main:create_app --factory --host 0.0.0.0 --port 8000
```

必须使用 `--factory`；模块导入不会创建应用或打开数据库连接。需要传入 `data_dir` 等参数时，请使用上面的 `simple-image serve` 命令。

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

系统会自动查找唯一的 admin 用户并交互式输入新密码。如果存在多个管理员账号，需通过 `--username` 指定。SQLite 位于本机磁盘时，服务运行期间也可以执行重置，无需重启；命令会显示实际数据库路径、重新读取数据库验证结果，并注销该管理员已有的登录会话：

```bash
simple-image reset-admin-password ./data --username admin
```

使用 MySQL 等外部数据库时，同样支持 `--database-url`：

```bash
simple-image reset-admin-password ./data \
  --database-url mysql+pymysql://root:password@127.0.0.1:3306/simple_image
```

## 备份

### SQLite

- 离线备份：先停止服务，再复制整个 `--data-dir` 目录。
- 在线备份：使用 SQLite backup API 或 `sqlite3` 的 `.backup` 命令。
- 服务运行时不要只复制 `database.db`；WAL 模式下，已提交的数据可能仍在 `database.db-wal` 中，`database.db-wal` 和 `database.db-shm` 都属于实时数据库状态。

### MySQL

数据库请使用 MySQL 自身的备份工具；图片文件仍需单独备份 `--data-dir/images`。
