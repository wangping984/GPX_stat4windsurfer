#!/bin/bash

# GPX_stat4windsurfer 自动化部署脚本
# 使用方法: sudo bash deploy.sh

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查是否为root用户
check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "此脚本需要root权限运行，请使用: sudo bash deploy.sh"
        exit 1
    fi
}

# 检查系统
check_system() {
    log_info "检查系统环境..."
    
    # 检查是否为Ubuntu/Debian系统
    if ! command -v apt &> /dev/null; then
        log_error "此脚本仅支持Ubuntu/Debian系统"
        exit 1
    fi
    
    # 检查Python3
    if ! command -v python3 &> /dev/null; then
        log_error "Python3未安装"
        exit 1
    fi
    
    log_info "系统环境检查通过"
}

# 安装系统依赖
install_system_deps() {
    log_info "安装系统依赖..."
    apt update
    apt install -y python3-venv python3-pip ufw
    log_info "系统依赖安装完成"
}

# 设置项目环境
setup_project() {
    PROJECT_DIR="/home/wp/webserv/GPX_stat4windsurfer"
    FLASK_DIR="$PROJECT_DIR/GPX_stat4windsurfer"
    
    log_info "设置项目环境..."
    
    # 检查项目目录是否存在
    if [ ! -d "$PROJECT_DIR" ]; then
        log_error "项目目录不存在: $PROJECT_DIR"
        exit 1
    fi
    
    # 创建虚拟环境
    if [ ! -d "$PROJECT_DIR/venv" ]; then
        log_info "创建Python虚拟环境..."
        cd "$PROJECT_DIR"
        python3 -m venv venv
    else
        log_warn "虚拟环境已存在，跳过创建"
    fi
    
    # 激活虚拟环境并安装依赖
    log_info "安装Python依赖..."
    cd "$PROJECT_DIR"
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    
    log_info "项目环境设置完成"
}

# 创建systemd服务
create_systemd_service() {
    log_info "创建systemd服务..."
    
    cat > /etc/systemd/system/gpx_stat.service << EOF
[Unit]
Description=Gunicorn instance to serve GPX_stat4windsurfer
After=network.target

[Service]
User=wp
Group=wp
WorkingDirectory=/home/wp/webserv/GPX_stat4windsurfer/GPX_stat4windsurfer
Environment="PATH=/home/wp/webserv/GPX_stat4windsurfer/venv/bin"
ExecStart=/home/wp/webserv/GPX_stat4windsurfer/venv/bin/gunicorn --workers 3 --bind 0.0.0.0:5000 app:app
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
    
    log_info "systemd服务文件创建完成"
}

# 启动服务
start_service() {
    log_info "启动服务..."
    
    # 重新加载systemd配置
    systemctl daemon-reload
    
    # 启动服务
    systemctl start gpx_stat
    
    # 设置开机自启
    systemctl enable gpx_stat
    
    # 检查服务状态
    if systemctl is-active --quiet gpx_stat; then
        log_info "服务启动成功"
    else
        log_error "服务启动失败"
        systemctl status gpx_stat
        exit 1
    fi
}

# 配置防火墙
setup_firewall() {
    log_info "配置防火墙..."
    
    # 检查ufw是否启用
    if ufw status | grep -q "Status: active"; then
        ufw allow 5000/tcp
        log_info "防火墙规则已添加"
    else
        log_warn "UFW防火墙未启用，跳过防火墙配置"
    fi
}

# 测试服务
test_service() {
    log_info "测试服务..."
    
    # 等待服务启动
    sleep 3
    
    # 测试本地访问
    if curl -s http://127.0.0.1:5000 > /dev/null; then
        log_info "本地服务测试通过"
    else
        log_error "本地服务测试失败"
        exit 1
    fi
    
    # 获取服务器IP
    SERVER_IP=$(hostname -I | awk '{print $1}')
    log_info "服务部署完成！"
    log_info "访问地址: http://$SERVER_IP:5000"
}

# 显示服务管理命令
show_management_commands() {
    echo ""
    log_info "服务管理命令:"
    echo "  查看服务状态: sudo systemctl status gpx_stat"
    echo "  查看服务日志: sudo journalctl -u gpx_stat -f"
    echo "  重启服务: sudo systemctl restart gpx_stat"
    echo "  停止服务: sudo systemctl stop gpx_stat"
    echo "  禁用开机自启: sudo systemctl disable gpx_stat"
    echo ""
}

# 主函数
main() {
    log_info "开始部署 GPX_stat4windsurfer..."
    
    check_root
    check_system
    install_system_deps
    setup_project
    create_systemd_service
    start_service
    setup_firewall
    test_service
    show_management_commands
    
    log_info "部署完成！"
}

# 执行主函数
main "$@" 