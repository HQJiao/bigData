#!/bin/bash
set -e

# 文档解析存储系统 — 一键启动脚本
# 用法: ./start.sh
# 停止:  ./start.sh --stop

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/document-parser-backend"
FRONTEND_DIR="$SCRIPT_DIR/big-data-frontend"
LLM_DIR="$SCRIPT_DIR/llm-service"
LOG_DIR="$SCRIPT_DIR/logs"
mkdir -p "$LOG_DIR"

CONDA_ENV="bigData"

# ─── 颜色输出 ───
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m'

info()  { echo -e "${BLUE}[INFO]${NC}  $1"; }
ok()    { echo -e "${GREEN}[OK]${NC}    $1"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; }

# ─── 停止服务 ───
if [ "$1" = "--stop" ]; then
    info "停止所有服务..."

    for port in 8000 8001 5173; do
        local_pid=$(lsof -i :$port -t 2>/dev/null | head -1)
        if [ -n "$local_pid" ]; then
            kill "$local_pid" 2>/dev/null && ok "已停止端口 $port (PID $local_pid)"
        fi
    done

    # Celery
    celery_pids=$(pgrep -f "celery.*src.core.celery" 2>/dev/null || true)
    if [ -n "$celery_pids" ]; then
        echo "$celery_pids" | xargs kill 2>/dev/null && ok "已停止 Celery"
    fi

    exit 0
fi

# ─── 检查前置条件 ───
info "检查前置条件..."

if ! docker info >/dev/null 2>&1; then
    error "Docker 未运行，请先启动 Docker Desktop"
    exit 1
fi
ok "Docker 运行中"

if ! conda env list | grep -q "$CONDA_ENV"; then
    error "conda 环境 '$CONDA_ENV' 不存在"
    exit 1
fi
ok "conda 环境 '$CONDA_ENV' 就绪"

# ─── 步骤 1: Docker 依赖服务 ───
info "检查 Docker 依赖服务..."
cd "$BACKEND_DIR"
if docker-compose ps --services 2>/dev/null | grep -q "postgres"; then
    ok "Docker 服务已在运行"
else
    docker-compose up -d 2>/dev/null
    ok "Docker 服务已启动"
fi

# ─── 辅助函数: 检查端口 ───
wait_for_port() {
    local port=$1 name=$2
    for i in $(seq 1 15); do
        if curl -s --connect-timeout 1 "http://localhost:$port/health" >/dev/null 2>&1; then
            ok "$name 启动成功 (端口 $port)"
            return 0
        fi
        sleep 1
    done
    warn "$name 启动超时，请查看日志: $LOG_DIR/"
    return 1
}

# ─── 步骤 2: 启动后端 ───
info "启动后端服务 (Uvicorn :8000)..."
cd "$BACKEND_DIR"
conda run -n "$CONDA_ENV" --no-capture-output uvicorn src.app.main:app --reload --port 8000 > "$LOG_DIR/uvicorn.log" 2>&1 &
echo $! > "$LOG_DIR/uvicorn.pid"
wait_for_port 8000 "后端"

# ─── 步骤 3: 启动 Celery Worker ───
info "启动 Celery Worker..."
cd "$BACKEND_DIR"
conda run -n "$CONDA_ENV" --no-capture-output celery -A src.core.celery worker -l info > "$LOG_DIR/celery.log" 2>&1 &
echo $! > "$LOG_DIR/celery.pid"
sleep 2
if pgrep -f "celery.*src.core.celery" >/dev/null 2>&1; then
    ok "Celery Worker 启动成功 (PID: $(cat $LOG_DIR/celery.pid))"
else
    error "Celery Worker 启动失败，请查看日志: $LOG_DIR/celery.log"
    exit 1
fi

# ─── 步骤 4: 启动 LLM Service ───
info "启动 LLM 服务 (Uvicorn :8001)..."
cd "$LLM_DIR"
conda run -n "$CONDA_ENV" --no-capture-output uvicorn src.app.main:app --reload --port 8001 > "$LOG_DIR/llm.log" 2>&1 &
echo $! > "$LOG_DIR/llm.pid"
wait_for_port 8001 "LLM 服务"

# ─── 步骤 5: 启动前端 ───
info "启动前端服务 (Vite :5173)..."
cd "$FRONTEND_DIR"
rm -rf node_modules/.vite  # 清除缓存确保加载最新代码
npm run dev > "$LOG_DIR/frontend.log" 2>&1 &
echo $! > "$LOG_DIR/frontend.pid"
sleep 3
if curl -s --connect-timeout 1 http://localhost:5173 >/dev/null 2>&1; then
    ok "前端启动成功 (端口 5173)"
else
    warn "前端启动中，请稍候..."
fi

# ─── 完成 ───
echo ""
echo -e "${GREEN}=== 服务已全部启动 ===${NC}"
echo -e "  前端(开发): ${BLUE}http://localhost:5173${NC}"
echo -e "  前端(生产): ${BLUE}http://localhost:8000${NC}"
echo -e "  API 文档:   ${BLUE}http://localhost:8000/docs${NC}"
echo -e "  LLM 服务:   ${BLUE}http://localhost:8001${NC}"
echo -e "  MinIO 面板: ${BLUE}http://localhost:9001${NC}"
echo ""
echo -e "  停止服务:   ${YELLOW}./start.sh --stop${NC}"
echo -e "  日志目录:   ${YELLOW}$LOG_DIR/${NC}"
