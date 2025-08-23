#!/bin/bash

# Lean4 前后端停止脚本
# 使用方法: ./stop.sh

echo "🛑 正在停止 Lean4 证明助手..."

# 定义颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. 停止 Flask 应用进程
echo -e "${YELLOW}🔍 查找 Flask 进程...${NC}"
FLASK_PIDS=$(ps aux | grep "python.*app.py" | grep -v grep | awk '{print $2}')

if [ ! -z "$FLASK_PIDS" ]; then
    echo -e "${RED}终止 Flask 进程: $FLASK_PIDS${NC}"
    echo $FLASK_PIDS | xargs kill -9 2>/dev/null || true
    echo -e "${GREEN}✅ Flask 进程已终止${NC}"
else
    echo -e "${BLUE}ℹ️  未找到运行中的 Flask 进程${NC}"
fi

# 2. 停止占用5001端口的进程
echo -e "${YELLOW}🔍 查找占用端口5001的进程...${NC}"
PORT_PIDS=$(lsof -ti:5001 2>/dev/null)

if [ ! -z "$PORT_PIDS" ]; then
    echo -e "${RED}终止占用端口5001的进程: $PORT_PIDS${NC}"
    echo $PORT_PIDS | xargs kill -9 2>/dev/null || true
    echo -e "${GREEN}✅ 端口5001已释放${NC}"
else
    echo -e "${BLUE}ℹ️  端口5001未被占用${NC}"
fi

# 3. 停止其他相关Python进程
echo -e "${YELLOW}🔍 查找其他相关进程...${NC}"
OTHER_PIDS=$(ps aux | grep "python.*lean" | grep -v grep | awk '{print $2}')

if [ ! -z "$OTHER_PIDS" ]; then
    echo -e "${RED}终止其他相关进程: $OTHER_PIDS${NC}"
    echo $OTHER_PIDS | xargs kill -9 2>/dev/null || true
    echo -e "${GREEN}✅ 其他相关进程已终止${NC}"
else
    echo -e "${BLUE}ℹ️  未找到其他相关进程${NC}"
fi

# 4. 等待进程完全停止
echo -e "${YELLOW}⏳ 等待进程完全停止...${NC}"
sleep 2

# 5. 最终检查
echo -e "${YELLOW}🔍 最终检查...${NC}"
REMAINING_FLASK=$(ps aux | grep "python.*app.py" | grep -v grep | wc -l)
REMAINING_PORT=$(lsof -ti:5001 2>/dev/null | wc -l)

if [ "$REMAINING_FLASK" -eq 0 ] && [ "$REMAINING_PORT" -eq 0 ]; then
    echo -e "${GREEN}✅ 所有进程已成功停止${NC}"
    echo -e "${GREEN}✅ 端口5001已释放${NC}"
else
    echo -e "${RED}⚠️  可能仍有进程在运行，请手动检查${NC}"
    if [ "$REMAINING_FLASK" -gt 0 ]; then
        echo -e "${RED}   仍有 Flask 进程在运行${NC}"
    fi
    if [ "$REMAINING_PORT" -gt 0 ]; then
        echo -e "${RED}   端口5001仍被占用${NC}"
    fi
fi

echo -e "${GREEN}🎉 停止脚本执行完成！${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}💡 如需重新启动，请运行: ./restart.sh${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"