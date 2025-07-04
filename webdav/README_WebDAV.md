# Ubuntu 24 WebDAV 服务配置脚本

本项目提供了三个不同的脚本来在Ubuntu 24上配置WebDAV服务，支持多用户权限管理。

## 脚本说明

### 1. `setup_webdav_apache.sh` (推荐)
- **服务器**: Apache
- **特点**: 支持真正的多用户权限控制
- **用户权限**:
  - `wangp` (密码: 123): 完全读写权限
  - `guestuser` (密码: 456): 只读权限

### 2. `setup_webdav_simple.sh`
- **服务器**: Nginx
- **特点**: 简化配置，所有用户具有相同权限
- **用户权限**: 所有认证用户都具有完全读写权限

### 3. `setup_webdav.sh`
- **服务器**: Nginx
- **特点**: 尝试实现权限控制（但Nginx限制较多）
- **注意**: 由于Nginx配置限制，可能无法完全实现权限分离

## 系统要求

- Ubuntu 24.04 LTS
- Root权限
- 网络连接（用于安装软件包）

## 使用方法

### 1. 下载脚本
```bash
# 确保脚本有执行权限
chmod +x setup_webdav_apache.sh
chmod +x setup_webdav_simple.sh
chmod +x setup_webdav.sh
```

### 2. 运行脚本
```bash
# 推荐使用Apache版本（支持真正的权限控制）
sudo ./setup_webdav_apache.sh

# 或者使用Nginx简化版本
sudo ./setup_webdav_simple.sh
```

### 3. 验证安装
脚本运行完成后，您将看到配置信息，包括：
- 服务端口: 6000
- 根目录: `/home/wp/webdav`
- 访问地址: `http://your-server-ip:6000`
- 用户凭据信息

## 配置详情

### 服务配置
- **端口**: 6000
- **根目录**: `/home/wp/webdav`
- **认证方式**: HTTP Basic Authentication
- **最大上传大小**: 100MB

### 用户配置
| 用户名 | 密码 | 权限 |
|--------|------|------|
| wangp | 123 | 完全读写 |
| guestuser | 456 | 只读 |

### 目录结构
```
/home/wp/webdav/
├── README.txt
└── 示例目录/
    └── 示例文件.txt
```

## 管理命令

### Apache版本
```bash
# 查看服务状态
systemctl status apache2

# 重启服务
systemctl restart apache2

# 查看访问日志
tail -f /var/log/apache2/webdav_access.log

# 查看错误日志
tail -f /var/log/apache2/webdav_error.log
```

### Nginx版本
```bash
# 查看服务状态
systemctl status nginx

# 重启服务
systemctl restart nginx

# 查看访问日志
tail -f /var/log/nginx/webdav_access.log

# 查看错误日志
tail -f /var/log/nginx/webdav_error.log
```

## 客户端连接

### Windows
1. 打开文件资源管理器
2. 右键点击"此电脑"
3. 选择"映射网络驱动器"
4. 输入地址: `http://your-server-ip:6000`
5. 输入用户名和密码

### macOS
1. 打开访达
2. 按 Cmd+K
3. 输入地址: `http://your-server-ip:6000`
4. 输入用户名和密码

### Linux
```bash
# 使用cadaver命令行客户端
sudo apt install cadaver
cadaver http://your-server-ip:6000

# 或使用图形界面客户端如Nautilus
```

## 故障排除

### 1. 端口被占用
```bash
# 检查端口使用情况
sudo netstat -tlnp | grep :6000

# 如果端口被占用，可以修改脚本中的端口号
```

### 2. 防火墙问题
```bash
# 检查防火墙状态
sudo ufw status

# 手动添加防火墙规则
sudo ufw allow 6000/tcp
```

### 3. 权限问题
```bash
# 检查目录权限
ls -la /home/wp/webdav

# 修复权限
sudo chown -R www-data:www-data /home/wp/webdav
sudo chmod -R 755 /home/wp/webdav
```

### 4. 服务无法启动
```bash
# 检查配置语法
# Apache
sudo apache2ctl configtest

# Nginx
sudo nginx -t

# 查看详细错误信息
sudo journalctl -u apache2 -f
sudo journalctl -u nginx -f
```

## 安全建议

1. **更改默认密码**: 脚本运行后立即更改用户密码
2. **使用HTTPS**: 在生产环境中配置SSL证书
3. **限制访问**: 配置防火墙只允许特定IP访问
4. **定期备份**: 定期备份WebDAV目录
5. **监控日志**: 定期检查访问日志

## 卸载

如果需要卸载WebDAV服务：

### Apache版本
```bash
sudo a2dissite webdav.conf
sudo systemctl restart apache2
sudo rm -rf /home/wp/webdav
sudo rm /etc/apache2/auth/webdav_users
```

### Nginx版本
```bash
sudo rm /etc/nginx/sites-enabled/webdav
sudo systemctl restart nginx
sudo rm -rf /home/wp/webdav
sudo rm /etc/nginx/auth/webdav_users
```

## 许可证

此脚本仅供学习和个人使用。在生产环境中使用前，请确保符合相关安全要求。

## 支持

如果遇到问题，请检查：
1. 系统日志
2. 服务状态
3. 网络连接
4. 防火墙配置 