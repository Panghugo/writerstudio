import os
import re
import time
import requests
import markdown
import json
from datetime import datetime

import path_utils

# ================= 🔧 初始化配置加载模块 =================
def load_config():
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
                print("✅ 已加载本地配置 (config.json)")
        except: pass
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

# ================= 🎨 样式装修队 =================
STYLE_CONFIG = {
    "body": """
        font-family: 'Optima-Regular', 'Optima', 'PingFang SC', 'HarmonyOS Sans', 'Noto Sans SC', 'Microsoft YaHei', sans-serif; 
        text-align: justify; 
        line-height: 1.8; 
        color: #333; 
        padding: 20px 8px;
        letter-spacing: 0.034em;
    """,
    "p": "margin-bottom: 32px; font-size: 16px;",
    
    # 分割线
    "separator": """
        text-align: center; 
        margin: 15px auto 20px auto;
        line-height: 1;
    """,
    
    # 导语盒子
    "summary": """
        font-size: 15px; 
        color: #666; 
        line-height: 1.7;
        text-align: justify; 
        padding: 20px 16px; 
        background-color: #f9f9f9; 
        border-radius: 6px;
        margin-bottom: 50px; 
    """,

    "img_card": "display: block; width: 100% !important; margin: 30px 0; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.08);", 
    "img_header": "display: block; width: 100% !important; margin: 0 0 5px 0; pointer-events: none;",
    "img_heading": "display: block; width: 100% !important; margin: 10px 0; pointer-events: none;",
    "img_footer": "display: block; width: 100% !important; margin: 50px 0 0 0; pointer-events: none;",
}

class WeChatPublisher:
    def __init__(self, app_id, app_secret):
        self.app_id = app_id
        self.app_secret = app_secret
        self.proxies = PROXY_CONFIG if USE_PROXY else None
        if USE_PROXY: print(f"🛡️ 已启用代理隧道")
        self.token = self.get_access_token()

    def get_access_token(self):
        if not self.app_id or not self.app_secret:
            print("❌ 错误：AppID 或 AppSecret 为空！")
            return None
        url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={self.app_id}&secret={self.app_secret}"
        try:
            resp = requests.get(url, proxies=self.proxies).json()
            if "access_token" in resp:
                print("✅ 微信 API 连接成功！")
                return resp["access_token"]
            else:
                print(f"❌ Token 获取失败: {resp}")
                return None
        except Exception as e:
            print(f"❌ 网络请求错误: {e}")
            return None

    def upload_image(self, file_path, is_thumb=False):
        if not os.path.exists(file_path): return None
        try:
            files = {'media': open(file_path, 'rb')}
            
            # 【修复点】这里分开了 URL 的拼接逻辑，防止出现两个问号
            if is_thumb:
                # 封面图：永久素材接口
                url = f"https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={self.token}&type=image"
                resp = requests.post(url, files=files, proxies=self.proxies).json()
                if "media_id" in resp:
                    print(f"   🖼️ 封面上传成功 [ID获取正常]")
                    return resp["media_id"]
            else:
                # 正文图：临时素材接口
                url = f"https://api.weixin.qq.com/cgi-bin/media/uploadimg?access_token={self.token}"
                resp = requests.post(url, files=files, proxies=self.proxies).json()
                if "url" in resp:
                    print(f"   ☁️ 图片上传成功: {os.path.basename(file_path)}")
                    return resp["url"]
            
            print(f"   ❌ 上传异常: {resp}")
            return None
        except Exception as e:
            print(f"   ❌ 网络错误: {e}")
            return None

    def md_to_wechat_html(self, md_content, assets_map):
        def process_bold_text(text):
            """将 Markdown 加粗语法 **文字** 转换为金黄色样式"""
            # 使用正则表达式匹配 **文字** 并替换为带样式的 span
            pattern = r'\*\*(.+?)\*\*'
            replacement = r'<span style="color: #E6C35C; font-weight: bold;">\1</span>'
            return re.sub(pattern, replacement, text)
        
        html = ""
        lines = md_content.splitlines()
        is_first_text_paragraph = True
        
        for line in lines:
            line = line.strip()
            if not line: continue
            
            if line.startswith("![]"):
                match = re.search(r'\((.*?)\)', line)
                if match:
                    local_path = match.group(1)
                    wechat_url = assets_map.get(local_path)
                    if wechat_url:
                        style = STYLE_CONFIG["img_card"]
                        if "HEADER" in local_path: style = STYLE_CONFIG["img_header"]
                        elif "FOOTER" in local_path: style = STYLE_CONFIG["img_footer"]
                        elif "H_" in local_path: style = STYLE_CONFIG["img_heading"]
                        html += f'<img src="{wechat_url}" style="{style}" />'
            else:
                clean_text = line.replace("# ", "").replace("## ", "").replace("> ", "")
                if clean_text:
                    # 处理加粗文本
                    clean_text = process_bold_text(clean_text)
                    
                    if is_first_text_paragraph:
                        print(f"   ✨ 识别到导语: {clean_text[:10]}...") 
                        
                        # 插入装饰分割线 - 使用section标签和明确的居中样式
                        separator_html = """
                        <section style="margin: 15px auto 20px auto; text-align: center; line-height: 1;">
                            <span style="display: inline-block; width: 40px; border-top: 1px solid #E6C35C; vertical-align: middle;"></span>
                            <span style="display: inline-block; width: 6px; height: 6px; background-color: #E6C35C; border-radius: 50%; vertical-align: middle; margin: 0 8px;"></span>
                            <span style="display: inline-block; width: 40px; border-top: 1px solid #E6C35C; vertical-align: middle;"></span>
                        </section>
                        """
                        html += separator_html
                        # 导语使用左侧金色边框标识，微信编辑器支持border属性
                        html += f'<section style="font-size: 15px; color: #666; line-height: 1.7; text-align: justify; padding: 20px 16px 20px 24px; border-left: 4px solid #E6C35C; background-color: #f9f9f9; margin-bottom: 50px;">{clean_text}</section>'
                        is_first_text_paragraph = False
                    else:
                        html += f'<p style="{STYLE_CONFIG["p"]}">{clean_text}</p>'
                    
        return f'<div style="{STYLE_CONFIG["body"]}">{html}</div>'

    def publish_draft(self, folder_name, author_name, base_output_dir="output"):
        base_dir = os.path.join(base_output_dir, folder_name)
        assets_dir = os.path.join(base_dir, "assets")
        md_file = os.path.join(base_dir, f"FINAL_{folder_name}.md")
        
        if not os.path.exists(md_file):
            print("❌ 找不到 Markdown 文件！")
            return
        if not self.token: return

        print(f"🚀 开始处理: {folder_name}")
        with open(md_file, 'r', encoding='utf-8') as f: content = f.read()

        assets_map = {}
        thumb_media_id = None
        
        for root, dirs, files in os.walk(assets_dir):
            for file in files:
                if file.lower().endswith(('.png', '.jpg', '.gif')):
                    local_path = os.path.join("assets", file).replace("\\", "/")
                    full_path = os.path.join(root, file)
                    
                    if "COVER" in file:
                        # 封面图
                        thumb_media_id = self.upload_image(full_path, is_thumb=True)
                    else:
                        # 正文图
                        url = self.upload_image(full_path, is_thumb=False)
                        if url: assets_map[local_path] = url

        # 检查封面是否上传成功
        if not thumb_media_id:
            print("⚠️ 警告: 未找到封面图或上传失败，草稿可能会没有封面。")

        final_html = self.md_to_wechat_html(content, assets_map)
        draft_url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={self.token}"
        title = folder_name.replace(".md", "")
        
        article_data = {
            "articles": [{
                "title": title, 
                "author": author_name, 
                "digest": "", 
                "content": final_html,
                "thumb_media_id": thumb_media_id if thumb_media_id else "", 
                "need_open_comment": 1
            }]
        }
        
        headers = {'Content-Type': 'application/json; charset=utf-8'}
        resp = requests.post(draft_url, data=json.dumps(article_data, ensure_ascii=False).encode('utf-8'), headers=headers, proxies=self.proxies)
        res_json = resp.json()
        
        if "media_id" in res_json:
            print("\n🎉🎉🎉 成功！草稿已发送到公众号后台！")
            print("👉 请登录 mp.weixin.qq.com -> 草稿箱 查看。")
        else:
            print(f"\n❌ 提交草稿失败: {res_json}")


# ================= 🚀 对外接口 =================
def run_publisher(target_folder, auth_name, app_id, app_secret, use_proxy=False, base_output_dir="output"):
    """供 GUI 调用的主函数"""
    global USE_PROXY
    USE_PROXY = use_proxy # Update global usage inside class for now, ideally refactor class too
    
    # Update PROXY_CONFIG in class instance if needed, but for now we rely on Init
    # Ideally we pass proxy config to init.
    
    uploader = WeChatPublisher(app_id, app_secret)
    # Monkey patch proxy if needed or refactor class completely. 
    # For minimal change:
    if use_proxy:
        uploader.proxies = PROXY_CONFIG
    else:
        uploader.proxies = None
        
    uploader.publish_draft(target_folder, auth_name, base_output_dir=base_output_dir)

if __name__ == "__main__":
    # Local CLI Test
    app_id = input("AppID: ").strip()
    app_secret = input("AppSecret: ").strip()
    uploader = WeChatPublisher(app_id, app_secret)
    target_folder = input("请输入文章文件夹名 (例如 test): ").strip()
    auth_name = input("请输入作者名: ").strip()
    uploader.publish_draft(target_folder, auth_name)