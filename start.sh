#!/bin/bash
set -e

# 文档解析存储系统 — 一键启动脚本
# 用法: ./start.sh
# 停止所有服务: ./start.sh --stop

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/document-parser-backend"
FRONTEND_DIR="$SCRIPT_DIR/big-data-frontend"
LOG_DIR="$SCRIPT_DIR/logs"
mkdir -p "$LOG_DIR"

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

    # 前端 Vite
    if [ -f "$LOG_DIR/frontend.pid" ]; then
        kill "$(cat "$LOG_DIR/frontend.pid")" 2>/dev/null && ok "已停止前端 (Vite)" || warn "前端未运行"
        rm -f "$LOG_DIR/frontend.pid"
    fi

    # Celery Worker
    if [ -f "$LOG_DIR/celery.pid" ]; then
        kill "$(cat "$LOG_DIR/celery.pid")" 2>/dev/null && ok "已停止 Celery Worker" || warn "Celery 未运行"
        rm -f "$LOG_DIR/celery.pid"
    fi

    # 后端 Uvicorn
    if [ -f "$LOG_DIR/uvicorn.pid" ]; then
        kill "$(cat "$LOG_DIR/uvicorn.pid")" 2>/dev/null && ok "已停止后端 (Uvicorn)" || warn "Uvicorn 未运行"
        rm -f "$LOG_DIR/uvicorn.pid"
    fi

    # Docker 可选停止
    read -p "是否也停止 Docker 服务 (PostgreSQL/Redis/MinIO)? [y/N]: " answer
    if [ "$answer" = "y" ] || [ "$answer" = "Y" ]; then
        cd "$BACKEND_DIR" && docker-compose down
        ok "已停止 Docker 服务"
    fi

    exit 0
fi

# ─── 检查前置条件 ───
info "检查前置条件..."

# 1. Docker 服务
if ! docker info >/dev/null 2>&1; then
    error "Docker 未运行，请先启动 Docker Desktop"
    exit 1
fi
ok "Docker 运行中"

# 2. Conda 环境
if ! conda activate bigData 2>/dev/null; then
    error "conda 环境 'bigData' 不存在"
    exit 1
fi
ok "conda 环境 'bigData' 就绪"

# ─── 步骤 1: Docker 依赖服务 ───
info "启动 Docker 依赖服务 (PostgreSQL/Redis/MinIO)..."
cd "$BACKEND_DIR"
docker-compose up -d 2>/dev/null
ok "Docker 服务已就绪"

# ─── 步骤 2: 检查端口占用 ───
check_port() {
    local port=$1 name=$2 pid_file=$3
    local pid
    pid=$(lsof -i :$port -t 2>/dev/null | head -1)
    if [ -n "$pid" ]; then
        # 尝试连接确认服务是否存活
        if curl -s --connect-timeout 1 http://localhost:$port/health >/dev/null 2>&1; then
            ok "$name 已在端口 $port 运行 (PID: $pid)，复用中"
            echo "$pid" > "$LOG_DIR/$pid_file"
            return 0
        else
            warn "端口 $port 被占用但服务无响应，清理旧进程..."
            kill -9 "$pid" 2>/dev/null || true
            sleep 1
            return 1
        fi
    fi
    return 1
}

# ─── 步骤 3: 启动后端 ───
info "启动后端服务 (Uvicorn :8000)..."
if ! check_port 8000 "后端" "uvicorn.pid"; then
    conda activate bigData >/dev/null 2>&1
    cd "$BACKEND_DIR"
    uvicorn src.app.main:app --reload --port 8000 > "$LOG_DIR/uvicorn.log" 2>&1 &
    echo $! > "$LOG_DIR/uvicorn.pid"

    # 等待启动
    for i in $(seq 1 15); do
        if curl -s --connect-timeout 1 http://localhost:8000/health >/dev/null 2>&1; then
            ok "后端启动成功 (PID: $(cat $LOG_DIR/uvicorn.pid))"
            break
        fi
        if [ "$i" -eq 15 ]; then
            error "后端启动超时，请查看日志: $LOG_DIR/uvicorn.log"
            exit 1
        fi
        sleep 1
    done
fi

# ─── 步骤 4: 启动 Celery Worker ───
info "启动 Celery Worker..."
if lsof -i :6379 -t >/dev/null 2>&1 && pgrep -f "celery.*src.core.celery" >/dev/null 2>&1; then
    CELERY_PID=$(pgrep -f "celery.*src.core.celery" | head -1)
    ok "Celery Worker 已在运行 (PID: $CELERY_PID)"
    echo "$CELERY_PID" > "$LOG_DIR/celery.pid"
else
    conda activate bigData >/dev/null 2>&1
    cd "$BACKEND_DIR"
    celery -A src.core.celery worker -l info > "$LOG_DIR/celery.log" 2>&1 &
    echo $! > "$LOG_DIR/celery.pid"
    sleep 3
    if pgrep -P "$(cat $LOG_DIR/celery.pid)" >/dev/null 2>&1; then
        ok "Celery Worker 启动成功 (PID: $(cat $LOG_DIR/celery.pid))"
    else
        error "Celery Worker 启动失败，请查看日志: $LOG_DIR/celery.log"
        exit 1
    fi
fi

# ─── 步骤 5: 启动前端 ───
info "启动前端服务 (Vite :5173)..."
if ! check_port 5173 "前端" "frontend.pid"; then
    cd "$FRONTEND_DIR"
    npm run dev > "$LOG_DIR/frontend.log" 2>&1 &
    echo $! > "$LOG_DIR/frontend.pid"
    sleep 3
    if curl -s --connect-timeout 1 http://localhost:5173 >/dev/null 2>&1; then
        ok "前端启动成功 (PID: $(cat $LOG_DIR/frontend.pid))"
    else
        error "前端启动失败，请查看日志: $LOG_DIR/frontend.log"
        exit 1
    fi
fi

# ─── 完成 ───
echo ""
echo -e "${GREEN}=== 服务已全部启动 ===${NC}"
echo -e "  后端 API:  ${BLUE}http://localhost:8000${NC}"
echo -e "  API 文档:  ${BLUE}http://localhost:8000/docs${NC}"
echo -e "  前端界面:  ${BLUE}http://localhost:5173${NC}"
echo -e "  MinIO 面板:${BLUE}http://localhost:9001${NC}"
echo ""
echo -e "  停止服务:  ${YELLOW}./start.sh --stop${NC}"
echo -e "  日志目录:  ${YELLOW}$LOG_DIR/${NC}"
