#!/bin/bash
# ============================================================
# GEE2OGE Web 服务守护脚本（无需 sudo）
# 功能：循环启动 gunicorn，进程退出后 5 秒自动重启
# 用法：nohup ./monitor.sh >> monitor.log 2>&1 &
# 停止：pkill -f monitor.sh && pkill -f gunicorn
# ============================================================

# 获取项目根目录（本脚本所在目录）
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WEB_DIR="$PROJECT_DIR/web"
LOG_FILE="$PROJECT_DIR/gunicorn.log"

# 自动查找 venv 位置（兼容 web/venv 和 项目根/venv 两种布局）
if [ -f "$WEB_DIR/venv/bin/gunicorn" ]; then
    GUNICORN_BIN="$WEB_DIR/venv/bin/gunicorn"
elif [ -f "$PROJECT_DIR/venv/bin/gunicorn" ]; then
    GUNICORN_BIN="$PROJECT_DIR/venv/bin/gunicorn"
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 错误：未找到 venv/bin/gunicorn，请先执行:" >> "$LOG_FILE"
    echo "  cd $WEB_DIR && python3 -m venv venv && source venv/bin/activate && pip install -r ../requirements.txt" >> "$LOG_FILE"
    exit 1
fi

cd "$WEB_DIR"

# 主循环：启动 -> 等待退出 -> 5秒后重启
while true; do
    echo "==========================================================" >> "$LOG_FILE"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 启动 gunicorn (端口 5001)..." >> "$LOG_FILE"

    # -w 4: 4 worker；-b 0.0.0.0:5001: 监听所有网卡
    # --timeout 600: 大于 LLM 的 420s 超时，避免长请求被杀
    # --access-logfile - : 访问日志输出到 stdout（合并到 gunicorn.log）
    "$GUNICORN_BIN" -w 4 -b 0.0.0.0:5001 --timeout 600 --access-logfile - app:app >> "$LOG_FILE" 2>&1

    EXIT_CODE=$?
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] gunicorn 退出 (exit=$EXIT_CODE)，5 秒后重启..." >> "$LOG_FILE"
    sleep 5
done
