"""Compatibility facade for legacy imports.

New code should import from writer_studio.wechat_publisher directly.
"""

from writer_studio.wechat_publisher import PROXY_CONFIG, WeChatPublisher, run_publisher


__all__ = ["PROXY_CONFIG", "WeChatPublisher", "run_publisher"]


if __name__ == "__main__":
    app_id = input("AppID: ").strip()
    app_secret = input("AppSecret: ").strip()
    uploader = WeChatPublisher(app_id, app_secret)
    target_folder = input("请输入文章文件夹名 (例如 test): ").strip()
    auth_name = input("请输入作者名: ").strip()
    uploader.publish_draft(target_folder, auth_name)
