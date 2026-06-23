#!/usr/bin/env bash
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

log_info()  { echo -e "${CYAN}[INFO]${NC}  $1"; }
log_ok()    { echo -e "${GREEN}[OK]${NC}    $1"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC}  $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo ""
echo -e "${CYAN}======================================${NC}"
echo -e "${CYAN}  One Person AI — 一键部署脚本${NC}"
echo -e "${CYAN}======================================${NC}"
echo ""

# ---------- 环境检测 ----------
log_info "检测系统环境..."

if ! command -v docker &>/dev/null; then
    log_error "Docker 未安装。请先安装 Docker："
    echo "  macOS: https://docs.docker.com/desktop/setup/install/mac-install/"
    echo "  Linux: curl -fsSL https://get.docker.com | bash"
    exit 1
fi
log_ok "Docker $(docker --version | grep -oP '\d+\.\d+\.\d+' | head -1)"

if ! docker compose version &>/dev/null; then
    log_error "Docker Compose 不可用。Docker Desktop 已内置 compose，请升级 Docker 版本。"
    exit 1
fi
log_ok "Docker Compose $(docker compose version --short 2>/dev/null || docker compose version 2>&1 | grep -oP '\d+\.\d+\.\d+')"

# ---------- 配置引导 ----------
echo ""
log_info "配置服务参数（直接回车使用默认值）"
echo ""

# DeepSeek API Key
DEFAULT_API_KEY=""
read -r -p "  DeepSeek API Key (必填, sk-...): " DEEPSEEK_API_KEY
if [ -z "$DEEPSEEK_API_KEY" ]; then
    log_error "DeepSeek API Key 不能为空，请先在 https://platform.deepseek.com/ 获取"
    exit 1
fi

# JWT Secret
DEFAULT_JWT="dev-secret-$(date +%s | md5sum 2>/dev/null | head -c 16 || date +%s | md5 2>/dev/null | head -c 16 || echo 'change-me')"
read -r -p "  JWT 密钥 (默认: $DEFAULT_JWT): " JWT_SECRET
JWT_SECRET="${JWT_SECRET:-$DEFAULT_JWT}"

# MySQL 密码
DEFAULT_MYSQL_PASS="ai_pass_$(openssl rand -base64 6 2>/dev/null || date +%s | head -c 8)"
read -r -p "  MySQL 密码 (默认: $DEFAULT_MYSQL_PASS): " MYSQL_PASS
MYSQL_PASS="${MYSQL_PASS:-$DEFAULT_MYSQL_PASS}"

# CORS
read -r -p "  前端域名 (默认: http://localhost:3000): " CORS_ORIGINS
CORS_ORIGINS="${CORS_ORIGINS:-http://localhost:3000}"

# ---------- 写入 .env ----------
echo ""
log_info "生成 .env 配置文件..."

cat > .env << EOF
# DeepSeek API 配置
DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY}

# JWT 配置
JWT_SECRET=${JWT_SECRET}
CORS_ORIGINS=${CORS_ORIGINS}

# MySQL 配置
MYSQL_ROOT_PASSWORD=root_${MYSQL_PASS}
MYSQL_PASSWORD=${MYSQL_PASS}

# 运行环境
APP_ENV=production
EOF

chmod 600 .env
log_ok ".env 文件已生成"

# ---------- 拉取并启动 ----------
echo ""
log_info "拉取 Docker 镜像并启动服务..."
log_info "首次启动需要下载依赖并构建，可能需要 3-8 分钟..."

if docker compose up -d --build 2>&1; then
    echo ""
    log_ok "所有容器已启动，正在检查健康状态..."
else
    log_error "服务启动失败，请查看上方错误信息"
    exit 1
fi

# ---------- 健康检查 ----------
MAX_RETRIES=30
RETRY_INTERVAL=3
HEALTHY=false

for i in $(seq 1 $MAX_RETRIES); do
    API_STATUS=$(curl -sf http://localhost:8000/health 2>/dev/null || echo "")
    FRONTEND_STATUS=$(curl -sf -o /dev/null -w "%{http_code}" http://localhost:3000 2>/dev/null || echo "")

    if [ "$API_STATUS" = '{"status":"healthy"}' ] && [ "$FRONTEND_STATUS" = "200" ]; then
        HEALTHY=true
        break
    fi
    echo -n "."
    sleep $RETRY_INTERVAL
done

echo ""

if [ "$HEALTHY" = true ]; then
    echo ""
    echo -e "${GREEN}======================================${NC}"
    echo -e "${GREEN}  🎉 部署完成！${NC}"
    echo -e "${GREEN}======================================${NC}"
    echo ""
    echo -e "  前端页面:  ${CYAN}http://localhost:3000${NC}"
    echo -e "  API 接口:  ${CYAN}http://localhost:8000${NC}"
    echo -e "  管理后台:  ${CYAN}http://localhost:3000/admin${NC}"
    echo ""
    echo -e "  API 文档:  ${CYAN}http://localhost:8000/docs${NC}"
    echo ""
    echo -e "  MySQL:     ${YELLOW}localhost:3306${NC}"
    echo "             用户名: ai_user"
    echo "             密码:   ${MYSQL_PASS}"
    echo ""
    echo -e "${YELLOW}  请将 http://localhost:3000 添加到浏览器书签${NC}"
    echo ""
else
    log_warn "服务未完全就绪，可能仍在启动中。请手动检查："
    echo "  docker compose ps"
    echo "  docker compose logs api-service"
fi
