import json
import os
import sys
from pathlib import Path

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from publisher import WeChatPublisher


class FakeWeChatClient:
    def __init__(self):
        self.last_error = ''
        self.uploaded = []
        self.article_data = None

    def ensure_token(self):
        return 'fake-token'

    def upload_image(self, file_path, is_thumb=False):
        self.uploaded.append((file_path, is_thumb))
        name = os.path.basename(file_path)
        if is_thumb:
            return 'fake-thumb-media-id'
        return f'https://fake.local/{name}'

    def add_draft(self, article_data):
        self.article_data = article_data
        return {'media_id': 'fake-draft-media-id'}


def find_latest_generated_draft():
    candidates = sorted(
        Path('temp_sessions').glob('*/output/*/FINAL_*.md'),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    if not candidates:
        candidates = sorted(
            Path('output').glob('*/FINAL_*.md'),
            key=lambda path: path.stat().st_mtime,
            reverse=True,
        )
    if not candidates:
        raise FileNotFoundError('No generated FINAL_*.md files found.')

    for final_md in candidates:
        assets_dir = final_md.parent / 'assets'
        if assets_dir.exists() and any(assets_dir.iterdir()):
            return final_md
    return candidates[0]


def run_check():
    final_md = find_latest_generated_draft()
    folder_name = final_md.parent.name
    base_output_dir = str(final_md.parent.parent)
    assets_dir = final_md.parent / 'assets'
    assets = sorted([path for path in assets_dir.glob('*') if path.is_file()]) if assets_dir.exists() else []

    uploader = WeChatPublisher('fake-app-id', 'fake-secret')
    fake_client = FakeWeChatClient()
    uploader.client = fake_client
    ok = uploader.publish_draft(
        folder_name,
        'Offline Tester',
        base_output_dir=base_output_dir,
        theme='black_gold',
    )

    article_data = fake_client.article_data or {}
    articles = article_data.get('articles') or []
    article = articles[0] if articles else {}
    content = article.get('content', '')
    uploadable_assets = [
        path for path in assets
        if path.suffix.lower() in {'.png', '.jpg', '.gif'}
    ]

    checks = {
        'publish_draft_returned_true': ok is True,
        'final_markdown_exists': final_md.exists(),
        'assets_dir_exists': assets_dir.exists(),
        'uploaded_asset_count_matches': len(fake_client.uploaded) == len(uploadable_assets),
        'article_data_has_one_article': len(articles) == 1,
        'article_has_title': bool(article.get('title')),
        'article_has_author': article.get('author') == 'Offline Tester',
        'article_content_non_empty': len(content) > 100,
        'article_content_has_wrapper': content.startswith('<div style='),
        'article_content_has_no_script_tag': '<script' not in content.lower(),
        'draft_submit_called': fake_client.article_data is not None,
    }

    summary = {
        'target_final_md': str(final_md),
        'folder_name': folder_name,
        'base_output_dir': base_output_dir,
        'asset_count': len(assets),
        'uploaded': [
            {'file': os.path.basename(path), 'is_thumb': is_thumb}
            for path, is_thumb in fake_client.uploaded
        ],
        'article_title': article.get('title'),
        'article_author': article.get('author'),
        'thumb_media_id': article.get('thumb_media_id'),
        'content_length': len(content),
        'checks': checks,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))

    failed = [name for name, passed in checks.items() if not passed]
    if failed:
        raise AssertionError(f'Offline publisher check failed: {", ".join(failed)}')


if __name__ == '__main__':
    run_check()
