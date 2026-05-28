# Writer Studio

Writer Studio 是一个本地 Flask Web App，用来写 Markdown 文章、生成公众号风格的 HTML/图片预览，并把草稿推送到微信公众号后台。它也支持从 Obsidian 加载文章、上传图片、同步到个人博客。

默认访问地址：

```text
http://localhost:5001
```

## 当前架构

后端入口很薄：

- `web.py`：本地服务入口，创建 Flask app 并启动服务。
- `writer_studio/web_app.py`：Flask app factory 和路由注册。
- `writer_studio/web_services.py`：Web 路由调用的业务服务层。
- `writer_studio/wechat_publisher.py`：微信公众号草稿发布编排。
- `writer_studio/wechat_client.py`：微信公众号 API 客户端。
- `writer_studio/wechat_draft.py`：素材扫描、上传和草稿数据构造。
- `writer_studio/pipeline.py`、`renderer.py`、`preview.py`、`themes.py`：文章生成、渲染和预览。

前端拆分在：

- `templates/index.html`：页面结构。
- `static/css/app.css`：样式。
- `static/js/dom.js`：页面元素引用。
- `static/js/editor.js`：编辑器文本格式插入。
- `static/js/generation.js`：保存 Markdown 并生成预览。
- `static/js/notifications.js`：顶部通知提示。
- `static/js/api.js`：后端 API 封装。
- `static/js/app.js`：前端入口和 UI 协调。
- `static/js/settings.js`：设置弹窗和配置读取。
- `static/js/publishing.js`：公众号发布和博客同步。
- `static/js/obsidian.js`：Obsidian 文件浏览和加载。
- `static/js/session.js`：浏览器会话 ID。
- `static/js/theme.js`：主题选择持久化。
- `static/js/uploads.js`：图片上传。

更多结构说明见 [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)。

## 启动

推荐使用本地虚拟环境：

```bash
cd /Users/hugo/Documents/Writer_Studio
./Start_Web.command
```

也可以直接运行：

```bash
cd /Users/hugo/Documents/Writer_Studio
./venv/bin/python3 web.py
```

如需登录后自动启动：

```bash
cd /Users/hugo/Documents/Writer_Studio
./scripts/install_autostart.sh
```

取消自动启动：

```bash
./scripts/uninstall_autostart.sh
```

更多服务说明见 [docs/WEB_SERVER_GUIDE.md](docs/WEB_SERVER_GUIDE.md)。

## 配置

本地配置文件是 `config.json`。如果不存在，可以从模板复制：

```bash
cp config.template.json config.json
```

可配置字段：

```json
{
  "app_id": "",
  "app_secret": "",
  "author_name": "作者",
  "use_proxy": 0,
  "obsidian_vault_path": "",
  "obsidian_attachments_folder": "attachments"
}
```

说明：

- `app_id`、`app_secret`：微信公众号后台的开发者凭证。
- `author_name`：默认作者名。
- `use_proxy`：是否让微信 API 请求走代理。
- `obsidian_vault_path`：Obsidian vault 路径。
- `obsidian_attachments_folder`：Obsidian 附件目录名。

页面设置会优先使用浏览器 `localStorage` 里的值；没有本地浏览器设置时，会读取服务端注入的 `config.json` 默认值。

## 检查

结构调整或发布链路修改后，先跑统一检查：

```bash
./venv/bin/python3 scripts/check_all.py
```

这个入口会执行：

- `compileall`：检查 `app.py`、`web.py`、`publisher.py`、`writer_studio`、`scripts` 是否能编译。
- `scripts/smoke_test.py`：Web 生成链路烟测。
- `scripts/check_text_formatting.py`：文本格式化检查。
- `scripts/check_publisher_offline.py`：公众号发布离线回归检查。
- `node --check static/js/*.js`：前端 JavaScript 语法检查；如果本机没有 `node`，会提示并跳过。

## 常见问题

端口 `5001` 被占用：

```bash
lsof -i :5001
kill -9 <PID>
```

查看服务日志：

```bash
tail -f web_server.log
tail -f web_server_error.log
```

公众号发布前请确认：

- `config.json` 或页面设置里有有效的 `app_id` 和 `app_secret`。
- 已经先生成文章预览，目标输出目录里存在 `FINAL_*.md`。
- 封面图和正文素材路径合法，素材文件存在。
- 微信后台开发者配置可用，且当前环境能访问微信 API。

如果页面提示“检查命令行日志了解上传失败详情”，优先查看 `web_server.log` 和 `web_server_error.log`。

## 运行时数据

这些路径是本地运行产物，不应提交：

```text
input/
output/
temp_sessions/
*.log
config.json
qtest.png
```

## 兼容入口

项目仍保留部分历史 wrapper，方便旧脚本或旧调用方式继续工作：

- `app.py`
- `publisher.py`
- `Auto_All.command`
- `Start_App.command`
- `WriterStudio_GUI.py`
- `blog_publisher.py`
- `run.command`

新代码优先使用 `writer_studio/` 内的模块。

## 维护文档

- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)：当前架构地图。
- [docs/CLEANUP_SUMMARY.md](docs/CLEANUP_SUMMARY.md)：清理记录。
- [docs/LEGACY_ENTRYPOINTS.md](docs/LEGACY_ENTRYPOINTS.md)：旧入口盘点。
- [docs/MIGRATION_NOTES.md](docs/MIGRATION_NOTES.md)：迁移说明。
- [docs/LOG_ROTATION_GUIDE.md](docs/LOG_ROTATION_GUIDE.md)：日志轮转。
- [docs/WEB_SERVER_GUIDE.md](docs/WEB_SERVER_GUIDE.md)：本地服务启动和排障。
