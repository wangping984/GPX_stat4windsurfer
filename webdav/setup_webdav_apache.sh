#!/bin/bash

# Ubuntu 24 Apache WebDAV 配置脚本
# 作者: Assistant
# 功能: 配置Apache WebDAV服务，支持多用户权限管理

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
    apt install -y apache2 apache2-utils
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
    mkdir -p /etc/apache2/auth
    
    # 创建用户密码文件
    htpasswd -c /etc/apache2/auth/webdav_users wangp <<< "123"
    htpasswd /etc/apache2/auth/webdav_users guestuser <<< "456"
    
    # 设置正确的权限
    chown www-data:www-data /etc/apache2/auth/webdav_users
    chmod 640 /etc/apache2/auth/webdav_users
}

# 创建Apache配置文件
create_apache_config() {
    log_info "创建Apache WebDAV配置文件..."
    
    cat > /etc/apache2/sites-available/webdav.conf << 'EOF'
<VirtualHost *:6000>
    ServerName webdav.local
    DocumentRoot /home/wp/webdav
    
    # 日志配置
    ErrorLog ${APACHE_LOG_DIR}/webdav_error.log
    CustomLog ${APACHE_LOG_DIR}/webdav_access.log combined
    
    # WebDAV配置
    <Directory /home/wp/webdav>
        Options Indexes MultiViews
        AllowOverride None
        Require all granted
        
        # 启用WebDAV
        Dav On
        
        # 基本认证
        AuthType Basic
        AuthName "WebDAV Access"
        AuthUserFile /etc/apache2/auth/webdav_users
        Require valid-user
        
        # 根据用户设置不同权限
        <RequireAny>
            <RequireAll>
                Require user wangp
                <LimitExcept GET HEAD OPTIONS PROPFIND>
                    Require user wangp
                </LimitExcept>
            </RequireAll>
            <RequireAll>
                Require user guestuser
                <Limit GET HEAD OPTIONS PROPFIND>
                    Require user guestuser
                </Limit>
            </RequireAll>
        </RequireAny>
    </Directory>
    
    # 禁止访问隐藏文件
    <DirectoryMatch "^/.*/\.">
        Require all denied
    </DirectoryMatch>
</VirtualHost>
EOF
}

# 启用必要的Apache模块
enable_apache_modules() {
    log_info "启用Apache模块..."
    a2enmod dav
    a2enmod dav_fs
    a2enmod auth_basic
    a2enmod authn_file
    a2enmod authz_user
    a2enmod authz_core
}

# 启用站点
enable_site() {
    log_info "启用WebDAV站点..."
    a2ensite webdav.conf
    
    # 禁用默认站点
    a2dissite 000-default.conf
}

# 配置Apache监听端口
configure_apache_port() {
    log_info "配置Apache监听端口..."
    
    # 备份原始配置
    cp /etc/apache2/ports.conf /etc/apache2/ports.conf.backup
    
    # 添加6000端口监听
    echo "Listen 6000" >> /etc/apache2/ports.conf
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
test_apache_config() {
    log_info "测试Apache配置..."
    if apache2ctl configtest; then
        log_info "Apache配置测试通过"
    else
        log_error "Apache配置测试失败"
        exit 1
    fi
}

# 重启服务
restart_services() {
    log_info "重启Apache服务..."
    systemctl restart apache2
    systemctl enable apache2
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
    log_info "=== Apache WebDAV配置完成 ==="
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
    echo "- 查看服务状态: systemctl status apache2"
    echo "- 重启服务: systemctl restart apache2"
    echo "- 查看日志: tail -f /var/log/apache2/webdav_access.log"
    echo "- 查看错误日志: tail -f /var/log/apache2/webdav_error.log"
    echo
    log_info "配置完成！"
}

# 主函数
main() {
    log_info "开始配置Apache WebDAV服务..."
    
    check_root
    update_system
    install_packages
    create_webdav_directory
    create_password_file
    create_apache_config
    enable_apache_modules
    configure_apache_port
    enable_site
    configure_firewall
    test_apache_config
    restart_services
    create_test_files
    show_config_info
}

# 运行主函数
main "$@" 