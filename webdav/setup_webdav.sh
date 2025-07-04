#!/bin/bash

# Ubuntu 24 Nginx WebDAV 配置脚本
# 作者: Assistant
# 功能: 配置Nginx WebDAV服务，支持多用户权限管理

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
        log_error "此脚本需要root权限运行"
        exit 1
    fi
}

# 更新系统包
update_system() {
    log_info "更新系统包..."
    apt update
    apt upgrade -y
}

# 安装必要的软件包
install_packages() {
    log_info "安装必要的软件包..."
    apt install -y nginx apache2-utils
}

# 创建WebDAV目录
create_webdav_directory() {
    log_info "创建WebDAV目录..."
    mkdir -p /home/wp/webdav
    chown -R www-data:www-data /home/wp/webdav
    chmod 755 /home/wp/webdav
}

# 创建用户密码文件
create_password_file() {
    log_info "创建用户密码文件..."
    
    # 创建密码文件目录
    mkdir -p /etc/nginx/auth
    
    # 创建用户密码文件
    htpasswd -c /etc/nginx/auth/webdav_users wangp <<< "123"
    htpasswd /etc/nginx/auth/webdav_users guestuser <<< "456"
    
    # 设置正确的权限
    chown www-data:www-data /etc/nginx/auth/webdav_users
    chmod 640 /etc/nginx/auth/webdav_users
}

# 创建Nginx配置文件
create_nginx_config() {
    log_info "创建Nginx WebDAV配置文件..."
    
    cat > /etc/nginx/sites-available/webdav << 'EOF'
server {
    listen 6000;
    server_name _;
    
    # WebDAV根目录
    root /home/wp/webdav;
    index index.html index.htm;
    
    # 客户端最大上传大小
    client_max_body_size 100M;
    
    # 启用WebDAV
    dav_methods PUT DELETE MKCOL COPY MOVE;
    dav_ext_methods PROPFIND OPTIONS;
    dav_access user:rw group:rw all:r;
    
    # 创建目录权限
    create_full_put_path on;
    
    # 自动创建索引
    autoindex on;
    autoindex_exact_size off;
    autoindex_localtime on;
    
    # 日志配置
    access_log /var/log/nginx/webdav_access.log;
    error_log /var/log/nginx/webdav_error.log;
    
    # 主目录配置
    location / {
        # 基本认证
        auth_basic "WebDAV Access";
        auth_basic_user_file /etc/nginx/auth/webdav_users;
        
        # 根据用户设置不同权限
        if ($remote_user = "wangp") {
            # wangp用户完全读写权限
            dav_methods PUT DELETE MKCOL COPY MOVE;
            dav_access user:rw group:rw all:r;
        }
        
        if ($remote_user = "guestuser") {
            # guestuser用户只读权限
            dav_methods GET HEAD PROPFIND OPTIONS;
            dav_access user:r group:r all:r;
        }
        
        # 默认权限（只读）
        dav_methods GET HEAD PROPFIND OPTIONS;
        dav_access user:r group:r all:r;
    }
    
    # 禁止访问隐藏文件
    location ~ /\. {
        deny all;
    }
}
EOF
}

# 启用站点
enable_site() {
    log_info "启用WebDAV站点..."
    ln -sf /etc/nginx/sites-available/webdav /etc/nginx/sites-enabled/
    
    # 删除默认站点（如果存在）
    if [[ -L /etc/nginx/sites-enabled/default ]]; then
        rm /etc/nginx/sites-enabled/default
    fi
}

# 配置防火墙
configure_firewall() {
    log_info "配置防火墙..."
    
    # 检查ufw是否安装
    if command -v ufw &> /dev/null; then
        ufw allow 6000/tcp
        log_info "防火墙规则已添加：允许端口6000"
    else
        log_warn "ufw未安装，请手动配置防火墙规则"
    fi
}

# 测试配置
test_nginx_config() {
    log_info "测试Nginx配置..."
    if nginx -t; then
        log_info "Nginx配置测试通过"
    else
        log_error "Nginx配置测试失败"
        exit 1
    fi
}

# 重启服务
restart_services() {
    log_info "重启Nginx服务..."
    systemctl restart nginx
    systemctl enable nginx
}

# 创建测试文件
create_test_files() {
    log_info "创建测试文件..."
    
    # 创建欢迎文件
    cat > /home/wp/webdav/README.txt << 'EOF'
欢迎使用WebDAV服务！

用户权限说明：
- wangp (密码: 123): 完全读写权限
- guestuser (密码: 456): 只读权限

访问地址: http://your-server-ip:6000
EOF
    
    # 创建示例目录
    mkdir -p /home/wp/webdav/示例目录
    echo "这是一个示例文件" > /home/wp/webdav/示例目录/示例文件.txt
    
    # 设置正确的权限
    chown -R www-data:www-data /home/wp/webdav
    chmod -R 755 /home/wp/webdav
}

# 显示配置信息
show_config_info() {
    log_info "=== WebDAV配置完成 ==="
    echo
    echo "服务信息："
    echo "- 端口: 6000"
    echo "- 根目录: /home/wp/webdav"
    echo "- 访问地址: http://$(hostname -I | awk '{print $1}'):6000"
    echo
    echo "用户信息："
    echo "- 用户名: wangp, 密码: 123 (完全读写权限)"
    echo "- 用户名: guestuser, 密码: 456 (只读权限)"
    echo
    echo "管理命令："
    echo "- 查看服务状态: systemctl status nginx"
    echo "- 重启服务: systemctl restart nginx"
    echo "- 查看日志: tail -f /var/log/nginx/webdav_access.log"
    echo "- 查看错误日志: tail -f /var/log/nginx/webdav_error.log"
    echo
    log_info "配置完成！"
}

# 主函数
main() {
    log_info "开始配置Nginx WebDAV服务..."
    
    check_root
    update_system
    install_packages
    create_webdav_directory
    create_password_file
    create_nginx_config
    enable_site
    configure_firewall
    test_nginx_config
    restart_services
    create_test_files
    show_config_info
}

# 运行主函数
main "$@" 