#!/bin/bash
# AVDC 一键启动脚本
# 功能：环境检查、依赖安装、配置检查、启动程序

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  AVDC - AV Data Capture (Kimi版)${NC}"
echo -e "${BLUE}  一键启动脚本${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# 检查Python环境
echo -e "${YELLOW}[1/5] 检查Python环境...${NC}"
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo -e "${RED}错误: 未找到Python，请安装Python 3.x${NC}"
    exit 1
fi

PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')
echo -e "${GREEN}✓ Python版本: $PYTHON_VERSION${NC}"

# 检查/创建虚拟环境
echo -e "${YELLOW}[2/5] 检查虚拟环境...${NC}"
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}  创建虚拟环境...${NC}"
    $PYTHON_CMD -m venv venv
fi

# 激活虚拟环境
echo -e "${GREEN}✓ 激活虚拟环境${NC}"
source venv/bin/activate

# 检查依赖
echo -e "${YELLOW}[3/5] 检查依赖...${NC}"
if ! python -c "import PyQt5" 2>/dev/null; then
    echo -e "${YELLOW}  安装依赖...${NC}"
    pip install -r py-require.txt -q || {
        echo -e "${YELLOW}  尝试单独安装核心依赖...${NC}"
        pip install PyQt5 cloudscraper requests pillow lxml beautifulsoup4 -q
    }
fi
echo -e "${GREEN}✓ 依赖已安装${NC}"

# 检查配置文件
echo -e "${YELLOW}[4/5] 检查配置文件...${NC}"
if [ ! -f "config.ini" ]; then
    echo -e "${YELLOW}  创建默认配置文件...${NC}"
    cat > config.ini << 'EOF'
[common]
main_mode = 1
website = javbus
no_file_move = 1

[language]
priority = sc,tc,ja

[translate]
enabled = 1
use_translated_title = 1
src_lang = ja
dest_lang = zh-cn

[actor]
download_actor_photo = 1
actor_photo_folder = .actors

[file_download]
nfo = 1
poster = 1
fanart = 1
thumb = 1
overwrite_nfo = 1

[proxy]
type = no
proxy = 
timeout = 10
retry = 5

[Name_Rule]
folder_name = number-actor-title-release
naming_media = number-actor-title
naming_file = number

[media]
media_type = .mp4|.avi|.rmvb|.wmv|.mov|.mkv|.flv|.ts|.webm|.MP4|.AVI|.RMVB|.WMV|.MOV|.MKV|.FLV|.TS|.WEBM
sub_type = .smi|.srt|.idx|.sub|.sup|.psb|.ssa|.ass|.txt|.usf|.xss|.ssf|.rt|.lrc|.sbv|.vtt|.ttml
media_path = 
EOF
fi

# 检查媒体路径
MEDIA_PATH=$(grep "^media_path" config.ini | cut -d'=' -f2 | tr -d ' ')
if [ -z "$MEDIA_PATH" ] || [ "$MEDIA_PATH" = "" ]; then
    echo -e "${YELLOW}⚠ 警告: 未设置媒体路径，请在config.ini中设置 media_path${NC}"
    echo -e "${YELLOW}  示例: media_path = /Users/username/Movies${NC}"
fi

echo -e "${GREEN}✓ 配置文件就绪${NC}"

# 系统检查
echo -e "${YELLOW}[5/5] 系统检查...${NC}"

# 检查是否有旧进程
if pgrep -f "AVDC_Main.py" > /dev/null; then
    echo -e "${YELLOW}  检测到旧进程，正在关闭...${NC}"
    pkill -f "AVDC_Main.py" 2>/dev/null || true
    sleep 1
fi

echo -e "${GREEN}✓ 系统就绪${NC}"
echo ""

# 启动程序
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}  启动 AVDC...${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 后台启动并记录日志
nohup python AVDC_Main.py > "Log/AVDC_$(date +%Y%m%d_%H%M%S).log" 2>&1 &
APP_PID=$!

sleep 2

if ps -p $APP_PID > /dev/null; then
    echo -e "${GREEN}✓ 程序已启动 (PID: $APP_PID)${NC}"
    echo ""
    echo -e "${YELLOW}使用说明:${NC}"
    echo "  1. 在GUI界面设置媒体路径"
    echo "  2. 点击'开始刮削'进行元数据刮削"
    echo "  3. 查看 Log/ 目录获取详细日志"
    echo ""
    echo -e "${YELLOW}快捷功能:${NC}"
    echo "  - 翻译功能: 自动翻译日文标题和简介"
    echo "  - 仅刮削模式: 不移动文件，仅生成元数据"
    echo "  - 演员头像: 自动下载到 .actors/ 文件夹"
    echo ""
    echo -e "${BLUE}日志文件: Log/AVDC_*.log${NC}"
else
    echo -e "${RED}✗ 程序启动失败，请检查日志${NC}"
    exit 1
fi
