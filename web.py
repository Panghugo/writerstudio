from writer_studio.web_app import create_app


app_server = create_app()


if __name__ == '__main__':
    print("✅ 已加载本地配置 (config.json)")
    print("🚀 Writer Studio Web Server (Cloud Mode) starting at http://localhost:5001")
    app_server.run(host='0.0.0.0', port=5001, debug=False, use_reloader=False)
