import json
import os
import time

import requests


REQUEST_HEADERS = {
    "User-Agent": "WriterStudio/1.0 (+https://mp.weixin.qq.com/)",
}


class WeChatClient:
    def __init__(self, app_id, app_secret, proxies=None):
        self.app_id = app_id
        self.app_secret = app_secret
        self.proxies = proxies
        self.token = None
        self.last_error = ""

    def get_access_token(self):
        if not self.app_id or not self.app_secret:
            self.last_error = "AppID 或 AppSecret 为空，请在设置里填写后再发布。"
            print(f"❌ {self.last_error}")
            return None

        url = (
            "https://api.weixin.qq.com/cgi-bin/token"
            f"?grant_type=client_credential&appid={self.app_id}&secret={self.app_secret}"
        )
        for attempt in range(2):
            try:
                response = requests.get(
                    url,
                    proxies=self.proxies,
                    timeout=15,
                    headers=REQUEST_HEADERS,
                )
                response.raise_for_status()
                resp = response.json()
            except Exception as e:
                self.last_error = f"连接微信 API 失败：{type(e).__name__}。请检查网络、代理或稍后重试。"
                print(f"❌ {self.last_error} (attempt {attempt + 1}/2)")
                if attempt == 0:
                    time.sleep(1)
                    continue
                return None

            if "access_token" in resp:
                print("✅ 微信 API 连接成功！")
                self.last_error = ""
                self.token = resp["access_token"]
                return self.token

            errcode = resp.get("errcode", "unknown")
            errmsg = resp.get("errmsg", "未知错误")
            self.last_error = f"Token 获取失败：{errcode} {errmsg}"
            print(f"❌ {self.last_error}")
            return None

    def ensure_token(self):
        if self.token:
            return self.token
        return self.get_access_token()

    def upload_image(self, file_path, is_thumb=False):
        if not os.path.exists(file_path):
            return None

        token = self.ensure_token()
        if not token:
            return None

        try:
            with open(file_path, 'rb') as media:
                files = {'media': media}

                if is_thumb:
                    url = f"https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={token}&type=image"
                    resp = requests.post(
                        url,
                        files=files,
                        proxies=self.proxies,
                        timeout=30,
                        headers=REQUEST_HEADERS,
                    ).json()
                    if "media_id" in resp:
                        print("   🖼️ 封面上传成功 [ID获取正常]")
                        return resp["media_id"]
                else:
                    url = f"https://api.weixin.qq.com/cgi-bin/media/uploadimg?access_token={token}"
                    resp = requests.post(
                        url,
                        files=files,
                        proxies=self.proxies,
                        timeout=30,
                        headers=REQUEST_HEADERS,
                    ).json()
                    if "url" in resp:
                        print(f"   ☁️ 图片上传成功: {os.path.basename(file_path)}")
                        return resp["url"]

            self.last_error = f"图片上传失败：{resp.get('errcode', 'unknown')} {resp.get('errmsg', resp)}"
            print(f"   ❌ {self.last_error}")
            return None
        except Exception as e:
            self.last_error = f"图片上传网络错误：{type(e).__name__}"
            print(f"   ❌ {self.last_error}")
            return None

    def add_draft(self, article_data):
        token = self.ensure_token()
        if not token:
            return None

        draft_url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={token}"
        headers = {'Content-Type': 'application/json; charset=utf-8'}
        try:
            resp = requests.post(
                draft_url,
                data=json.dumps(article_data, ensure_ascii=False).encode('utf-8'),
                headers=headers,
                proxies=self.proxies,
                timeout=30,
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            self.last_error = f"提交草稿网络错误：{type(e).__name__}"
            print(f"\n❌ {self.last_error}")
            return None
