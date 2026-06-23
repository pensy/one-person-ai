# 部署指南

One Person AI — AI 工具聚合平台，支持 Docker 一键部署。

---

## 环境要求

| 组件 | 要求 |
|---|---|
| **Docker** | ≥ 24.0 |
| **Docker Compose** | ≥ 2.20 |
| **内存** | ≥ 2GB（含 MySQL） |
| **磁盘** | ≥ 5GB |
| **操作系统** | Linux / macOS / Windows (WSL2) |

---

## 快速开始

### 方式一：一键部署脚本（推荐）

```bash
cd deploy
bash quick-start.sh
```

脚本会引导输入配置，自动检测环境并启动服务。

### 方式二：手动部署

```bash
cd deploy

# 创建 .env 文件（参考下面的配置说明）
vim .env

# 启动
docker compose up -d --build

# 检查状态
docker compose ps
```

---

## 配置说明

### .env 文件

| 变量 | 必填 | 说明 |
|---|---|---|
| `DEEPSEEK_API_KEY` | 是 | DeepSeek API Key，在 [platform.deepseek.com](https://platform.deepseek.com/) 获取 |
| `JWT_SECRET` | 否 | 用户认证密钥，生产环境请修改为随机字符串 |
| `CORS_ORIGINS` | 否 | 前端域名，默认 `http://localhost:3000` |
| `MYSQL_ROOT_PASSWORD` | 否 | MySQL root 密码 |
| `MYSQL_PASSWORD` | 否 | MySQL 普通用户密码 |
| `APP_ENV` | 否 | `development` 或 `production` |

### 端口

| 服务 | 端口 |
|---|---|
| 前端页面 | `3000` |
| API 接口 | `8000` |
| Worker (gRPC) | `50051` |
| MySQL | `3306`（仅内部） |

---

## 服务说明

```
前端 (Next.js)  :3000  →  API 服务 (FastAPI)  :8000  →  Worker (Go gRPC)  :50051
                                              ↘  MySQL  :3306
```

- **前端**：Next.js 页面，浏览器直接访问
- **API 服务**：Python FastAPI，处理业务逻辑和认证
- **Worker 服务**：Go gRPC，异步执行 LLM 调用
- **MySQL**：数据存储

---

## 管理后台

启动后访问 `http://localhost:3000/admin`：

- 查看服务运行状态
- 启用/禁用 AI 工具
- 查看用户列表

---

## 运维命令

```bash
# 查看日志
docker compose logs api-service     # API 服务日志
docker compose logs worker-service   # Worker 日志
docker compose logs frontend         # 前端日志
docker compose logs mysql            # MySQL 日志

# 重启单个服务
docker compose restart api-service

# 更新后重新构建
docker compose up -d --build

# 停止所有服务
docker compose down

# 彻底清除（删数据库）
docker compose down -v
```

---

## 常见问题

### Q: 启动后页面空白或无法访问
检查服务是否全部启动：
```bash
docker compose ps
```
如果 MySQL 没启动，等待 10-20 秒后重试。

### Q: 工具调用失败，提示 AI 没 Key
检查 DeepSeek API Key 是否配置正确：
```bash
docker exec ai-tools-api env | grep DEEPSEEK_API_KEY
```
如果为空，在 `deploy/.env` 中设置 `DEEPSEEK_API_KEY` 后重启：
```bash
docker compose restart api-service worker-service
```

### Q: 端口冲突
修改 `docker-compose.yml` 中对应服务的 `ports` 映射，例如：
```yaml
ports:
  - "8080:8000"   # 把 API 端口改为 8080
```

### Q: 如何升级？
```bash
cd deploy
git pull
docker compose up -d --build
```

### Q: 数据备份
MySQL 数据在 Docker 卷 `deploy_mysql_data` 中：
```bash
docker run --rm -v deploy_mysql_data:/data -v $(pwd):/backup alpine tar czf /backup/mysql-backup.tar.gz -C /data .
```
