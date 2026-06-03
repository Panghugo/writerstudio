import os

from .renderers.wechat_article import markdown_to_wechat_html


# 微信图文素材只接受 png/jpg/jpeg/gif。这里有意比 config.ALLOWED_IMAGE_EXTENSIONS 更窄：
# Web 端允许用户上传 webp/svg 用于本地预览，但微信不支持，扫描素材上传时会跳过它们。
UPLOADABLE_IMAGE_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.gif')


def upload_assets(assets_dir, upload_image):
    assets_map = {}
    thumb_media_id = None

    for root, _dirs, files in os.walk(assets_dir):
        for file in files:
            if not file.lower().endswith(UPLOADABLE_IMAGE_EXTENSIONS):
                continue

            local_path = os.path.join("assets", file).replace("\\", "/")
            full_path = os.path.join(root, file)

            if "COVER" in file:
                thumb_media_id = upload_image(full_path, is_thumb=True)
            else:
                url = upload_image(full_path, is_thumb=False)
                if url:
                    assets_map[local_path] = url

    return assets_map, thumb_media_id


def build_article_data(folder_name, author_name, md_content, assets_map, thumb_media_id, theme="black_gold"):
    final_html = markdown_to_wechat_html(md_content, assets_map, theme=theme)
    title = folder_name.replace(".md", "")
    return {
        "articles": [{
            "title": title,
            "author": author_name,
            "digest": "",
            "content": final_html,
            "thumb_media_id": thumb_media_id if thumb_media_id else "",
            "need_open_comment": 1,
        }]
    }
