import os
import json

import path_utils
from writer_studio.wechat_client import WeChatClient
from writer_studio.wechat_draft import build_article_data, upload_assets
from writer_studio.wechat_format import markdown_to_wechat_html

# ================= 🔧 初始化配置加载模块 =================
def load_config(verbose=False):
    config_path = path_utils.get_external_path("config.json")
    default_config = {
        "app_id": "",
        "app_secret": "",
        "author_name": "",
        "use_proxy": False
    }
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                default_config.update(json.load(f))
                if verbose:
                    print("✅ 已加载本地配置 (config.json)")
        except Exception:
            pass
    return default_config

CONFIG = load_config()
APP_ID = CONFIG["app_id"]
APP_SECRET = CONFIG["app_secret"]
DEFAULT_AUTHOR = CONFIG["author_name"]
USE_PROXY = CONFIG["use_proxy"]

PROXY_CONFIG = {
    "http": "socks5://127.0.0.1:7890",
    "https": "socks5://127.0.0.1:7890"
}

class WeChatPublisher:
    def __init__(self, app_id=None, app_secret=None):
        self.app_id = app_id or APP_ID
        self.app_secret = app_secret or APP_SECRET
        self.proxies = PROXY_CONFIG if USE_PROXY else None
        self.last_error = ""
        self.client = WeChatClient(self.app_id, self.app_secret, proxies=self.proxies)
        if USE_PROXY: print(f"🛡️ 已启用代理隧道")

    def get_access_token(self):
        token = self.client.get_access_token()
        self.last_error = self.client.last_error
        return token

    def upload_image(self, file_path, is_thumb=False):
        result = self.client.upload_image(file_path, is_thumb=is_thumb)
        self.last_error = self.client.last_error
        return result

    def md_to_wechat_html(self, md_content, assets_map, theme="black_gold"):
        return markdown_to_wechat_html(md_content, assets_map, theme)

    def publish_draft(self, folder_name, author_name, base_output_dir="output", theme="black_gold"):
        base_dir = os.path.join(base_output_dir, folder_name)
        assets_dir = os.path.join(base_dir, "assets")
        md_file = os.path.join(base_dir, f"FINAL_{folder_name}.md")
        
        if not os.path.exists(md_file):
            self.last_error = f"找不到已生成的公众号草稿文件，请先点击 Generate。期待路径: {md_file}"
            print(f"❌ {self.last_error}")
            return False

        if not self.client.ensure_token():
            self.last_error = self.client.last_error
            return False

        print(f"🚀 开始处理: {folder_name}")
        with open(md_file, 'r', encoding='utf-8') as f: content = f.read()

        assets_map, thumb_media_id = upload_assets(assets_dir, self.upload_image)

        # 检查封面是否上传成功
        if not thumb_media_id:
            print("⚠️ 警告: 未找到封面图或上传失败，草稿可能会没有封面。")

        article_data = build_article_data(
            folder_name,
            author_name,
            content,
            assets_map,
            thumb_media_id,
            theme=theme,
        )
        
        res_json = self.client.add_draft(article_data)
        self.last_error = self.client.last_error
        if not res_json:
            return False
        
        if "media_id" in res_json:
            print("\n🎉🎉🎉 成功！草稿已发送到公众号后台！")
            print("👉 请登录 mp.weixin.qq.com -> 草稿箱 查看。")
            self.last_error = ""
            return True
        else:
            self.last_error = f"提交草稿失败：{res_json.get('errcode', 'unknown')} {res_json.get('errmsg', res_json)}"
            print(f"\n❌ {self.last_error}")
            return False


# ================= 🚀 对外接口 =================
def run_publisher(target_folder, auth_name, app_id, app_secret, use_proxy=False, base_output_dir="output", theme="black_gold"):
    """供 GUI 调用的主函数"""
    global USE_PROXY
    USE_PROXY = use_proxy
    
    uploader = WeChatPublisher(app_id, app_secret)
    if use_proxy:
        uploader.proxies = PROXY_CONFIG
    else:
        uploader.proxies = None
    uploader.client.proxies = uploader.proxies
        
    uploader.publish_draft(target_folder, auth_name, base_output_dir=base_output_dir, theme=theme)

if __name__ == "__main__":
    # Local CLI Test
    app_id = input("AppID: ").strip()
    app_secret = input("AppSecret: ").strip()
    uploader = WeChatPublisher(app_id, app_secret)
    target_folder = input("请输入文章文件夹名 (例如 test): ").strip()
    auth_name = input("请输入作者名: ").strip()
    uploader.publish_draft(target_folder, auth_name)
