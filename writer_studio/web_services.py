import os
import re
import subprocess
import threading
import uuid
import zipfile

import app
from PIL import Image
from scripts.plugins import blog_publisher

from .artifacts import html_artifact, image_artifact, output_url, zip_artifact
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
from .renderers.social_cards import create_social_cards, extract_social_image_text
from .themes import build_style
from .wechat_publisher import WeChatPublisher


GENERATION_LOCK = threading.Lock()
MARKDOWN_IMAGE_PATTERN = re.compile(r'^!\[(.*?)\]\((.*?)\)(?:\{[^}]*\})?$')
SOCIAL_PRESETS = {
    "balanced": {
        "label": "图文均衡",
        "style": {},
    },
    "longform": {
        "label": "长文连载",
        "style": {
            "social_font_size": 34,
            "social_line_height": 53,
            "social_paragraph_gap": 30,
            "social_margin_x": 84,
            "social_image_square_scale": 0.72,
            "social_image_portrait_scale": 0.52,
            "social_image_max_height": 0.42,
        },
    },
    "image_first": {
        "label": "图片优先",
        "style": {
            "social_font_size": 34,
            "social_line_height": 54,
            "social_paragraph_gap": 42,
            "social_image_square_scale": 0.9,
            "social_image_portrait_scale": 0.66,
            "social_image_max_height": 0.58,
            "social_image_square_max_height": 0.56,
            "social_image_portrait_max_height": 0.64,
        },
    },
    "quote_digest": {
        "label": "观点摘录",
        "style": {
            "social_font_size": 40,
            "social_line_height": 64,
            "social_paragraph_gap": 50,
            "social_margin_x": 92,
            "social_image_square_scale": 0.68,
            "social_image_portrait_scale": 0.5,
            "social_image_max_height": 0.38,
        },
    },
}


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

    preview_url = output_url(session_id, filename, preview_html)
    return {
        "status": "success",
        "preview_url": preview_url,
        "output_type": "wechat_article",
        "artifacts": [html_artifact(preview_url, preview_html)],
        "message": "Generated successfully!",
    }


def generate_social_image(data):
    filename = sanitize_name(data.get('filename', 'untitled'), 'untitled')
    session_id = str(data.get('session_id') or '').strip()
    theme = normalize_theme(data.get('theme'))
    author_name = str(data.get('author_name') or '作者').strip()
    content = data.get('content') or ''

    input_dir, output_dir = get_session_paths(session_id)
    output_folder = safe_child_path(output_dir, filename)
    assets_dir = safe_child_path(output_folder, "assets")
    os.makedirs(assets_dir, exist_ok=True)

    style = build_style(theme, author_name)
    apply_social_brand_overrides(style, data)
    social_preset = normalize_social_preset(data.get('social_preset'))
    apply_social_preset(style, social_preset)
    layout_overrides = normalize_layout_overrides(data.get('social_layout_overrides'))
    block_controls = normalize_block_controls(data.get('social_block_controls'))
    quality_checks = build_social_quality_checks(content, [input_dir, assets_dir])
    image_paths, page_layout = create_social_cards(
        content,
        assets_dir,
        style,
        image_dirs=[input_dir, assets_dir],
        layout_overrides=layout_overrides,
        block_controls=block_controls,
        return_metadata=True,
    )
    image_names = [os.path.basename(path) for path in image_paths]

    image_urls = [
        output_url(session_id, filename, f"assets/{image_name}")
        for image_name in image_names
    ]
    artifacts = [
        image_artifact(url, image_name, index=index, total=len(image_urls))
        for index, (url, image_name) in enumerate(zip(image_urls, image_names), start=1)
    ]
    zip_name = create_social_zip(output_folder, image_paths, filename)
    zip_url = output_url(session_id, filename, zip_name)
    artifacts.append(zip_artifact(zip_url, zip_name, count=len(image_paths)))
    quality_checks.extend(build_social_post_checks(content, image_paths))
    return {
        "status": "success",
        "image_url": image_urls[0],
        "image_urls": image_urls,
        "zip_url": zip_url,
        "zip_filename": zip_name,
        "page_count": len(image_urls),
        "output_type": "social_cards",
        "artifacts": artifacts,
        "quality_checks": quality_checks,
        "page_layout": page_layout,
        "social_preset": social_preset,
        "message": f"文字图已生成，共 {len(image_urls)} 张",
    }


def apply_social_brand_overrides(style, data):
    brand_name = str(data.get('social_brand_name') or '').strip()
    brand_en = str(data.get('social_brand_en') or '').strip()
    accent_text = str(data.get('social_brand_accent_text') or '').strip()

    if brand_name:
        style["brand_name"] = brand_name
    if brand_en:
        style["brand_en"] = brand_en
    if accent_text:
        style["social_brand_accent_text"] = accent_text


def normalize_social_preset(preset):
    preset_name = str(preset or 'balanced').strip()
    return preset_name if preset_name in SOCIAL_PRESETS else 'balanced'


def apply_social_preset(style, preset):
    style.update(SOCIAL_PRESETS.get(preset, SOCIAL_PRESETS["balanced"])["style"])


def normalize_layout_overrides(raw_overrides):
    if not isinstance(raw_overrides, dict):
        return {}
    normalized = {}
    for key, value in raw_overrides.items():
        if not isinstance(value, dict):
            continue
        normalized[str(key)] = {
            "layout": str(value.get("layout") or "auto"),
            "size": str(value.get("size") or "auto"),
            "show_caption": value.get("show_caption", True) is not False,
            "zoom": clamp_number(value.get("zoom"), 100, 180, 100),
            "crop_x": clamp_number(value.get("crop_x"), -100, 100, 0),
            "crop_y": clamp_number(value.get("crop_y"), -100, 100, 0),
            "margin_top": clamp_number(value.get("margin_top"), 0, 120, 0),
            "margin_bottom": clamp_number(value.get("margin_bottom"), 0, 120, 0),
        }
    return normalized


def normalize_block_controls(raw_controls):
    if not isinstance(raw_controls, dict):
        return {}
    normalized = {}
    for key, value in raw_controls.items():
        if not isinstance(value, dict):
            continue
        normalized[str(key)] = {
            "order": clamp_number(value.get("order"), 0, 999, clamp_number(key, 0, 999, 0)),
            "page_break_before": bool(value.get("page_break_before")),
            "keep_with_next": bool(value.get("keep_with_next")),
        }
    return normalized


def clamp_number(value, minimum, maximum, default):
    try:
        number = int(float(value))
    except (TypeError, ValueError):
        return default
    return max(minimum, min(maximum, number))


def create_social_zip(output_folder, image_paths, filename):
    zip_name = f"{sanitize_name(filename, 'social_cards')}_social_cards.zip"
    zip_path = safe_child_path(output_folder, zip_name)
    with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        for image_path in image_paths:
            archive.write(image_path, arcname=os.path.basename(image_path))
    return zip_name


def build_social_quality_checks(content, image_dirs):
    checks = []
    images = extract_markdown_images(content)
    text_length = len(strip_markdown_for_quality(content))

    if text_length < 120:
        checks.append(quality_check('info', '正文偏短，可能更适合做单图或金句卡片。'))
    if not images:
        checks.append(quality_check('info', '当前正文没有插入图片，会生成纯文字长图。'))

    for image in images:
        if len(image["alt"]) > 42:
            checks.append(quality_check('warning', f'图片说明「{image["alt"][:16]}...」偏长，可能挤压正文空间。'))
        image_path = resolve_quality_image_path(image["src"], image_dirs)
        if not image_path:
            checks.append(quality_check('error', f'找不到图片：{image["src"]}'))
            continue
        try:
            with Image.open(image_path) as source:
                width, height = source.size
        except Exception:
            checks.append(quality_check('error', f'图片无法读取：{image["src"]}'))
            continue
        if max(width, height) < 900:
            checks.append(quality_check('warning', f'图片「{image["src"]}」分辨率偏低，生成后可能发虚。'))
        if width / height < 0.42 or width / height > 2.4:
            checks.append(quality_check('info', f'图片「{image["src"]}」比例较极端，建议生成后检查裁切位置。'))
    return checks


def build_social_post_checks(content, image_paths):
    checks = []
    page_count = len(image_paths)
    if page_count > 9:
        checks.append(quality_check('warning', f'已生成 {page_count} 张，接近小红书多图发布上限，建议检查是否需要拆成两篇。'))
    elif page_count >= 6:
        checks.append(quality_check('info', f'已生成 {page_count} 张，建议检查每页信息密度。'))
    return checks


def extract_markdown_images(content):
    images = []
    for raw_line in content.splitlines():
        match = MARKDOWN_IMAGE_PATTERN.match(raw_line.strip())
        if match:
            images.append({
                "alt": match.group(1).strip(),
                "src": match.group(2).strip(),
            })
    return images


def strip_markdown_for_quality(content):
    lines = []
    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line or MARKDOWN_IMAGE_PATTERN.match(line):
            continue
        lines.append(re.sub(r'[#>*_`-]', '', line))
    return ''.join(lines)


def resolve_quality_image_path(src, image_dirs):
    if not src or src.startswith(("http://", "https://")):
        return None
    normalized = src.replace("\\", "/").lstrip("/")
    for image_dir in image_dirs:
        for candidate_name in [normalized, os.path.basename(normalized)]:
            candidate = os.path.abspath(os.path.join(image_dir, candidate_name))
            if os.path.exists(candidate):
                return candidate
    return None


def quality_check(level, message):
    return {"level": level, "message": message}


def open_output_folder(data):
    filename = sanitize_name(data.get('filename', 'untitled'), 'untitled')
    session_id = str(data.get('session_id') or '').strip()
    _, output_dir = get_session_paths(session_id)
    output_folder = safe_child_path(output_dir, filename)
    if not os.path.isdir(output_folder):
        raise FileNotFoundError("输出目录不存在，请先生成内容")
    subprocess.Popen(['open', output_folder])
    return {"status": "success", "message": "已打开输出目录"}


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

    uploader = WeChatPublisher(app_id, app_secret)
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


def remove_feature_image(data):
    session_id = str(data.get('session_id') or '').strip()
    input_dir, _ = get_session_paths(session_id)
    removed = []
    for ext in ['.png', '.jpg', '.jpeg']:
        path = safe_child_path(input_dir, f'feature{ext}')
        if os.path.exists(path):
            os.remove(path)
            removed.append(os.path.basename(path))
    return {
        "status": "success",
        "removed": removed,
        "message": "头图已移除" if removed else "当前没有头图",
    }


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
