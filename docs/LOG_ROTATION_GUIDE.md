# 日志轮转配置说明

## ✅ 已完成配置

Writer Studio 的日志系统现在已经配置了自动轮转功能。

---

## 📋 配置详情

### 日志文件
- **主日志**: `web_server.log` - 记录所有 INFO 级别及以上的日志
- **错误日志**: `web_server_error.log` - 只记录 ERROR 级别的日志

### 轮转策略
- **单文件大小限制**: 10MB
- **备份数量**: 3 个
- **总空间占用**: 约 30MB（主日志 + 错误日志各 4 个文件）

### 轮转机制
当日志文件达到 10MB 时，系统会自动：
1. 将当前日志重命名为 `web_server.log.1`
2. 创建新的 `web_server.log`
3. 旧的备份文件依次重命名（`.1` → `.2` → `.3`）
4. 最老的备份（`.3`）会被删除

---

## 📊 日志格式

新的日志格式包含更多信息：
```
2026-01-16 09:31:13,806 - werkzeug - INFO - * Debugger PIN: 216-545-142
```

格式说明：
- `2026-01-16 09:31:13,806` - 时间戳（精确到毫秒）
- `werkzeug` - 日志来源（模块名）
- `INFO` - 日志级别
- 后面是具体的日志消息

---

## 🔍 查看日志

### 实时查看日志
```bash
tail -f /Users/hugo/Documents/Writer_Studio/web_server.log
```

### 查看最近的日志
```bash
tail -50 /Users/hugo/Documents/Writer_Studio/web_server.log
```

### 查看错误日志
```bash
cat /Users/hugo/Documents/Writer_Studio/web_server_error.log
```

### 查看所有日志文件
```bash
ls -lh /Users/hugo/Documents/Writer_Studio/*.log*
```

---

## 💡 优势

1. **防止磁盘占满**: 日志不会无限增长
2. **自动管理**: 无需手动清理日志
3. **保留历史**: 保留最近 3 个备份，方便排查问题
4. **结构化**: 带时间戳和级别，便于分析

---

## 🎯 下一步

日志轮转已经配置完成，现在可以讨论您提到的其他想法了！

---

📅 配置时间: 2026-01-16 09:31
