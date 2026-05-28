import os
import threading
import uuid
from urllib.parse import quote

import app
import publisher
from scripts.plugins import blog_publisher

from .config import ALLOWED_IMAGE_EXTENSIONS, ALLOWED_THEMES, load_server_config
from .file_safety import (
    get_session_paths,
    safe_child_path,
    sanitize_name,
    sanitize_session_id,
)
from .obsidian import (
    list_markdown_files as list_obsidian_markdown_files,
    load_markdown_file as load_obsidian_markdown_file,
)


GENERATION_LOCK = threading.Lock()


def normalize_theme(theme):
    theme_name = str(theme or 'black_gold').strip()
    return theme_name if theme_name in ALLOWED_THEMES else 'black_gold'


def generate_preview(data):
    filename = sanitize_name(data.get('filename', 'untitled'), 'untitled')
    session_id = str(data.get('session_id') or '').strip()
    theme = normalize_theme(data.get('theme'))
    author_name = str(data.get('author_name') or '作者').strip()
    content = data.get('content') or ''

    input_dir, output_dir = get_session_paths(session_id)
    os.makedirs(input_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)

    md_file = f"{filename}.md"
    md_path = safe_child_path(input_dir, md_file)
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(content)

    with GENERATION_LOCK:
        app.main(
            target_md=md_file,
            input_dir=input_dir,
            output_dir=output_dir,
            theme=theme,
            author_name=author_name,
        )

    preview_html = find_preview_html(output_dir, filename)
    if not preview_html:
        return {
            "status": "warning",
            "message": "Generation completed but preview file not found."
        }

    preview_url = "/output/{}/{}/{}".format(
        quote(sanitize_session_id(session_id), safe=''),
        quote(filename, safe=''),
        quote(preview_html, safe=''),
    )
    return {
        "status": "success",
        "preview_url": preview_url,
        "message": "Generated successfully!",
    }


def find_preview_html(output_dir, filename):
    output_folder = safe_child_path(output_dir, filename)
    if not os.path.exists(output_folder):
        return None

    for name in os.listdir(output_folder):
        if name.startswith("PREVIEW_") and name.endswith(".html"):
            return name
    return None


def publish_wechat(data):
    filename = sanitize_name(data.get('filename', ''), '')
    if not filename:
        raise ValueError("Filename is required")

    session_id = str(data.get('session_id') or '').strip()
    app_id = str(data.get('app_id') or '').strip()
    app_secret = str(data.get('app_secret') or '').strip()
    author_name = str(data.get('author_name') or '').strip()
    theme = normalize_theme(data.get('theme'))

    _, output_dir = get_session_paths(session_id)
    folder_name = os.path.splitext(filename)[0]

    uploader = publisher.WeChatPublisher(app_id, app_secret)
    success = uploader.publish_draft(
        folder_name,
        author_name,
        base_output_dir=output_dir,
        theme=theme,
    )

    if success:
        return {"status": "success", "message": "Draft published successfully!"}

    return {
        "status": "error",
        "message": uploader.last_error or "发布失败，请检查 AppID/AppSecret、网络和生成文件。",
    }


def save_uploaded_image(file, session_id, is_feature=False):
    if not file or file.filename == '':
        raise ValueError('No selected file')

    input_dir, _ = get_session_paths(session_id)
    os.makedirs(input_dir, exist_ok=True)

    if is_feature:
        return save_feature_image(file, input_dir)
    return save_content_image(file, input_dir)


def save_feature_image(file, input_dir):
    for old_ext in ['.png', '.jpg', '.jpeg']:
        old_path = os.path.join(input_dir, f'feature{old_ext}')
        if os.path.exists(old_path):
            try:
                os.remove(old_path)
            except Exception:
                pass

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ['.png', '.jpg', '.jpeg']:
        ext = '.png'

    filename = f'feature{ext}'
    file.save(safe_child_path(input_dir, filename))
    return filename


def save_content_image(file, input_dir):
    original_name = sanitize_name(file.filename, 'image')
    stem, ext = os.path.splitext(original_name)
    if ext.lower() not in ALLOWED_IMAGE_EXTENSIONS:
        raise ValueError('Unsupported image type')

    filename = f"{stem[:60]}_{uuid.uuid4().hex[:8]}{ext.lower()}"
    file.save(safe_child_path(input_dir, filename))
    return filename


def publish_blog(data):
    content = data.get('content', '')
    filename = sanitize_name(data.get('filename', 'Untitled'), 'Untitled')
    author = str(data.get('author_name') or 'Hugo').strip()
    path = blog_publisher.publish_to_blog(filename, content, author)

    def run_deploy():
        blog_publisher.deploy_to_github(commit_message=f"Post: {filename}")

    threading.Thread(target=run_deploy).start()
    return {
        "status": "success",
        "message": f"Saved to {path}. 🚀 Syncing to GitHub...",
        "path": path,
    }


def get_obsidian_vault_path():
    config = load_server_config()
    if not config:
        raise FileNotFoundError("配置文件不存在")

    vault_path = config.get('obsidian_vault_path', '')
    if not vault_path or not os.path.exists(vault_path):
        raise FileNotFoundError("Obsidian 文件夹路径未配置或不存在")

    return vault_path


def list_obsidian_files():
    return list_obsidian_markdown_files(get_obsidian_vault_path())


def load_obsidian_file(data):
    filename = str(data.get('filename') or '').strip()
    session_id = str(data.get('session_id') or '').strip()
    if not filename:
        raise ValueError("文件名不能为空")

    input_dir, _ = get_session_paths(session_id)
    content, base_filename = load_obsidian_markdown_file(
        filename,
        get_obsidian_vault_path(),
        input_dir,
    )
    return {
        "content": content,
        "filename": base_filename,
    }
