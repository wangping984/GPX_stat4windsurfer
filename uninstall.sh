#!/bin/bash

# GPX_stat4windsurfer 卸载脚本
# 使用方法: sudo bash uninstall.sh

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

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
        log_error "此脚本需要root权限运行，请使用: sudo bash uninstall.sh"
        exit 1
    fi
}

# 停止并删除服务
remove_service() {
    log_info "停止并删除systemd服务..."
    
    # 停止服务
    if systemctl is-active --quiet gpx_stat; then
        systemctl stop gpx_stat
        log_info "服务已停止"
    fi
    
    # 禁用服务
    if systemctl is-enabled --quiet gpx_stat; then
        systemctl disable gpx_stat
        log_info "服务已禁用"
    fi
    
    # 删除服务文件
    if [ -f /etc/systemd/system/gpx_stat.service ]; then
        rm /etc/systemd/system/gpx_stat.service
        systemctl daemon-reload
        log_info "服务文件已删除"
    fi
}

# 清理防火墙规则
cleanup_firewall() {
    log_info "清理防火墙规则..."
    
    if ufw status | grep -q "Status: active"; then
        ufw delete allow 5000/tcp 2>/dev/null || log_warn "防火墙规则不存在或已删除"
    fi
}

# 清理项目文件（可选）
cleanup_project() {
    PROJECT_DIR="/home/wp/webserv/GPX_stat4windsurfer"
    
    echo ""
    read -p "是否删除项目文件？(y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log_warn "删除项目目录: $PROJECT_DIR"
        rm -rf "$PROJECT_DIR"
        log_info "项目文件已删除"
    else
        log_info "保留项目文件"
    fi
}

# 主函数
main() {
    log_info "开始卸载 GPX_stat4windsurfer..."
    
    check_root
    remove_service
    cleanup_firewall
    cleanup_project
    
    log_info "卸载完成！"
}

# 执行主函数
main "$@" 