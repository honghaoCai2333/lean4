#!/bin/bash

# Lean4 前后端重启脚本
# 使用方法: ./restart.sh

echo "🔧 正在重启 Lean4 证明助手..."

# 获取项目根目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 定义颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}📂 项目目录: $SCRIPT_DIR${NC}"

# 1. 停止现有进程
echo -e "${YELLOW}🛑 停止现有进程...${NC}"

# 查找并终止 Flask 应用进程
FLASK_PID=$(ps aux | grep "python.*app.py" | grep -v grep | awk '{print $2}')
if [ ! -z "$FLASK_PID" ]; then
    echo -e "${RED}终止 Flask 进程 (PID: $FLASK_PID)${NC}"
    kill -9 $FLASK_PID 2>/dev/null || true
fi

# 查找并终止占用5001端口的进程
PORT_PID=$(lsof -ti:5001)
if [ ! -z "$PORT_PID" ]; then
    echo -e "${RED}终止占用端口5001的进程 (PID: $PORT_PID)${NC}"
    kill -9 $PORT_PID 2>/dev/null || true
fi

# 等待进程完全停止
sleep 2

# 2. 检查虚拟环境
echo -e "${YELLOW}🔍 检查虚拟环境...${NC}"
if [ -d "lean4_env" ]; then
    echo -e "${GREEN}✅ 找到虚拟环境: lean4_env${NC}"
    source lean4_env/bin/activate
    echo -e "${GREEN}✅ 虚拟环境已激活${NC}"
else
    echo -e "${RED}❌ 未找到虚拟环境 lean4_env${NC}"
    echo -e "${YELLOW}请确保虚拟环境存在并已安装必要依赖${NC}"
    exit 1
fi

# 3. 检查配置文件
echo -e "${YELLOW}🔍 检查配置文件...${NC}"
if [ -f "config/config.yaml" ]; then
    echo -e "${GREEN}✅ 配置文件存在${NC}"
else
    echo -e "${RED}❌ 配置文件不存在: config/config.yaml${NC}"
    exit 1
fi

# 4. 检查必要文件
echo -e "${YELLOW}🔍 检查必要文件...${NC}"
REQUIRED_FILES=(
    "app.py"
    "lean_explore_direct_client.py"
    "front/chat.html"
    "database.py"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✅ $file${NC}"
    else
        echo -e "${RED}❌ $file 不存在${NC}"
        exit 1
    fi
done

# 5. 启动后端服务
echo -e "${YELLOW}🚀 启动后端服务...${NC}"
echo -e "${BLUE}后端将在 http://localhost:5001 启动${NC}"

# 使用 nohup 在后台启动，输出重定向到日志文件
nohup python app.py > app.log 2>&1 &
BACKEND_PID=$!

echo -e "${GREEN}✅ 后端已启动 (PID: $BACKEND_PID)${NC}"

# 6. 等待后端启动完成
echo -e "${YELLOW}⏳ 等待后端启动完成...${NC}"
sleep 5

# 7. 检查后端是否正常运行
echo -e "${YELLOW}🔍 检查后端状态...${NC}"
if curl -s http://localhost:5001/health > /dev/null; then
    echo -e "${GREEN}✅ 后端健康检查通过${NC}"
else
    echo -e "${RED}❌ 后端启动失败，请检查日志文件 app.log${NC}"
    tail -10 app.log
    exit 1
fi

# 8. 显示访问信息
echo -e "${GREEN}🎉 重启完成！${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}📍 访问地址:${NC}"
echo -e "${BLUE}   前端: http://localhost:5001${NC}"
echo -e "${BLUE}   API: http://localhost:5001/api/${NC}"
echo -e "${GREEN}📍 进程信息:${NC}"
echo -e "${BLUE}   后端 PID: $BACKEND_PID${NC}"
echo -e "${GREEN}📍 日志文件:${NC}"
echo -e "${BLUE}   app.log - 查看后端日志${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# 9. 提供管理命令
echo -e "${YELLOW}📋 管理命令:${NC}"
echo -e "${BLUE}   查看后端日志: tail -f app.log${NC}"
echo -e "${BLUE}   停止后端: kill $BACKEND_PID${NC}"
echo -e "${BLUE}   重启: ./restart.sh${NC}"

# 10. 可选：自动打开浏览器
read -p "是否自动打开浏览器? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if command -v open &> /dev/null; then
        open http://localhost:5001
    elif command -v xdg-open &> /dev/null; then
        xdg-open http://localhost:5001
    else
        echo -e "${YELLOW}无法自动打开浏览器，请手动访问: http://localhost:5001${NC}"
    fi
fi

echo -e "${GREEN}✨ 重启脚本执行完成！${NC}"