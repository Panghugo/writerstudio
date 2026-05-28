import hashlib
import logging
import os
import re
import shutil
import time
from urllib.parse import urlparse

import requests

from .file_safety import is_under_any, safe_child_path


def list_markdown_files(vault_path):
    files = []
    for filename in os.listdir(vault_path):
        if filename.endswith('.md') and not filename.startswith('.'):
            filepath = os.path.join(vault_path, filename)
            stat = os.stat(filepath)
            files.append({
                'name': filename,
                'size': stat.st_size,
                'modified': stat.st_mtime,
                'modified_str': time.strftime('%Y-%m-%d %H:%M', time.localtime(stat.st_mtime)),
            })

    files.sort(key=lambda x: x['modified'], reverse=True)
    return files


def load_markdown_file(filename, vault_path, input_dir):
    if not filename:
        raise ValueError('文件名不能为空')
    if '..' in filename or '/' in filename or '\\' in filename:
        raise ValueError('非法文件名')

    filepath = safe_child_path(vault_path, filename)
    if not os.path.exists(filepath):
        raise FileNotFoundError('文件不存在')

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    return process_images(content, vault_path, input_dir), os.path.splitext(filename)[0]


def process_images(content, vault_path, input_dir):
    """Process Obsidian image references and copy/download images to input directory."""
    os.makedirs(input_dir, exist_ok=True)

    obsidian_pattern = r'!\[\[([^\]]+\.(png|jpg|jpeg|gif|webp|svg))\]\]'
    url_pattern = r'!\[([^\]]*)\]\((https?://[^\)]+)\)'

    def replace_obsidian_image(match):
        image_name = match.group(1)
        vault_parent = os.path.dirname(vault_path)

        possible_paths = [
            os.path.join(vault_path, image_name),
            os.path.join(vault_path, 'attachments', image_name),
            os.path.join(vault_path, 'assets', image_name),
            os.path.join(vault_path, 'images', image_name),
            os.path.join(vault_parent, image_name),
            os.path.join(vault_parent, 'attachments', image_name),
            os.path.join(vault_parent, 'assets', image_name),
            os.path.join(vault_parent, 'images', image_name),
        ]

        source_path = None
        allowed_roots = [vault_path, vault_parent]
        for path in possible_paths:
            if os.path.exists(path) and is_under_any(path, allowed_roots):
                source_path = path
                break

        if not source_path:
            logging.warning('Local image not found: %s (searched %s locations)', image_name, len(possible_paths))
            return match.group(0)

        dest_filename = os.path.basename(image_name)
        dest_path = safe_child_path(input_dir, dest_filename)
        try:
            shutil.copy2(source_path, dest_path)
            logging.info('Copied local image: %s from %s', image_name, source_path)
            return f'![{os.path.splitext(dest_filename)[0]}]({dest_filename})'
        except Exception as e:
            logging.error('Failed to copy image %s: %s', image_name, e)
            return match.group(0)

    def replace_url_image(match):
        alt_text = match.group(1)
        image_url = match.group(2)

        is_image_url = (
            re.search(r'\.(png|jpg|jpeg|gif|webp|svg)($|\?|#)', image_url, re.IGNORECASE) or
            'imageUrl=' in image_url or
            'image' in image_url.lower() or
            '/mmbiz_' in image_url
        )
        if not is_image_url:
            return match.group(0)

        try:
            parsed_url = urlparse(image_url)
            ext_match = re.search(r'\.(png|jpg|jpeg|gif|webp|svg)', parsed_url.path, re.IGNORECASE)
            if ext_match:
                ext = ext_match.group(0)
            elif 'wx_fmt=png' in image_url or 'format=png' in image_url:
                ext = '.png'
            elif 'wx_fmt=jpeg' in image_url or 'wx_fmt=jpg' in image_url or 'format=jpg' in image_url:
                ext = '.jpg'
            else:
                ext = '.png'

            url_hash = hashlib.md5(image_url.encode()).hexdigest()[:8]
            dest_filename = f'downloaded_{url_hash}{ext}'
            dest_path = safe_child_path(input_dir, dest_filename)

            if os.path.exists(dest_path):
                logging.info('Image already downloaded: %s', dest_filename)
                return f'![{alt_text or "图片"}]({dest_filename})'

            logging.info('Downloading image from: %s...', image_url[:100])
            response = requests.get(image_url, timeout=15, headers={
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                'Referer': 'https://mp.weixin.qq.com/',
            })
            response.raise_for_status()

            content_type = response.headers.get('Content-Type', '')
            if not content_type.startswith('image/'):
                logging.warning('URL does not return image content: %s', content_type)
                return match.group(0)

            with open(dest_path, 'wb') as f:
                f.write(response.content)

            logging.info('Successfully downloaded: %s (%s bytes)', dest_filename, len(response.content))
            return f'![{alt_text or "图片"}]({dest_filename})'
        except Exception as e:
            logging.error('Failed to download image from %s: %s', image_url[:100], e)
            return match.group(0)

    processed_content = re.sub(obsidian_pattern, replace_obsidian_image, content, flags=re.IGNORECASE)
    return re.sub(url_pattern, replace_url_image, processed_content, flags=re.IGNORECASE)
