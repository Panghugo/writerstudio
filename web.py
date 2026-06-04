import os

from writer_studio.web_app import create_app


app_server = create_app()


if __name__ == '__main__':
    # 默认只监听本机，避免在局域网上无鉴权暴露（本服务处理公众号凭证、文件，且可触发 git push）。
    # 需要局域网或其它机器访问时，显式设置 WRITER_STUDIO_HOST=0.0.0.0。
    # 注意：Docker 镜像用 gunicorn --bind 0.0.0.0 启动，不走这里，因此不受影响。
    host = os.environ.get('WRITER_STUDIO_HOST', '127.0.0.1')
    port = int(os.environ.get('WRITER_STUDIO_PORT', '5001'))
    print("✅ 已加载本地配置 (config.json)")
    print(f"🚀 Writer Studio Web Server starting at http://{host}:{port}")
    app_server.run(host=host, port=port, debug=False, use_reloader=False)
