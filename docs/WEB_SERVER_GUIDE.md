# Writer Studio Web Server 使用指南

## 📍 项目位置

项目现在位于：`/Users/hugo/Documents/Writer_Studio`

> **注意**: 项目已从 Desktop 移动到 Documents 目录，以避免 macOS launchd 的权限限制。

---

## 两种启动方式

Writer Studio 现在主要通过本地 Web 应用运行，你可以根据需求选择：

### 方式 1: 开机自动启动 (推荐) ⭐

使用 macOS launchd 服务，让 Web 服务器在登录时自动启动。

**安装:**
```bash
cd /Users/hugo/Documents/Writer_Studio
./scripts/install_autostart.sh
```

**卸载:**
```bash
./scripts/uninstall_autostart.sh
```

**优点:**
- ✅ 开机自动启动，无需手动操作
- ✅ 崩溃自动重启
- ✅ 独立运行，不依赖旧桌面 GUI
- ✅ 可以直接将 http://localhost:5001 保存为书签

**查看状态:**
```bash
launchctl list | grep writerstudio
```

**查看日志:**
```bash
tail -f /Users/hugo/Documents/Writer_Studio/web_server.log
```

---

### 方式 2: 手动启动

使用现有的 `Start_Web.command` 脚本手动启动。

**使用方法:**
```bash
./Start_Web.command
```

**优点:**
- ✅ 简单直接
- ✅ 适合临时使用
- ✅ 自动打开浏览器

---

## 推荐配置

**最佳体验:** 使用方式 1 (开机自动启动)

1. 运行安装脚本:
   ```bash
   cd /Users/hugo/Documents/Writer_Studio
   ./scripts/install_autostart.sh
   ```

2. 将 http://localhost:5001 保存为浏览器书签

3. 以后只需点击书签即可访问！

## 故障排除

### 端口被占用
如果看到 "Address already in use" 错误，说明端口 5001 已被占用。

**查找占用进程:**
```bash
lsof -i :5001
```

**停止进程:**
```bash
kill -9 <PID>
```

### 服务无法启动
检查日志文件:
```bash
cat /Users/hugo/Documents/Writer_Studio/web_server.log
cat /Users/hugo/Documents/Writer_Studio/web_server_error.log
```

### 重启服务 (launchd)
```bash
launchctl kickstart -k gui/$(id -u)/com.writerstudio.webserver
```

---

## 技术说明

**为什么使用直接 Python 执行？**

macOS 的 launchd 服务对某些目录（如 Desktop）有严格的权限限制。为了避免这些问题：
1. 项目已移至 `~/Documents/Writer_Studio`
2. launchd 直接调用项目虚拟环境里的 Python 解释器
3. 这样可以确保服务稳定运行，不受权限限制影响
