import json
import os
import sys
import tempfile
from pathlib import Path

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from publisher import WeChatPublisher
from writer_studio.wechat_client import WeChatClient


class FakeWeChatClient:
    def __init__(self, token='fake-token', upload_fail_names=None, draft_response=None):
        self.last_error = ''
        self.token = token
        self.upload_fail_names = set(upload_fail_names or [])
        self.draft_response = draft_response or {'media_id': 'fake-draft-media-id'}
        self.uploaded = []
        self.article_data = None
        self.ensure_token_calls = 0

    def ensure_token(self):
        self.ensure_token_calls += 1
        if not self.token:
            self.last_error = 'fake token failure'
            return None
        return self.token

    def upload_image(self, file_path, is_thumb=False):
        self.uploaded.append((file_path, is_thumb))
        name = os.path.basename(file_path)
        if name in self.upload_fail_names:
            self.last_error = f'fake upload failure: {name}'
            return None
        if is_thumb:
            return 'fake-thumb-media-id'
        return f'https://fake.local/{name}'

    def add_draft(self, article_data):
        self.article_data = article_data
        return self.draft_response


def write_file(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding='utf-8')


def write_asset(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b'fake image bytes')


def make_case(root, folder_name, markdown=None, assets=None):
    case_dir = root / folder_name
    assets_dir = case_dir / 'assets'
    if markdown is not None:
        write_file(case_dir / f'FINAL_{folder_name}.md', markdown)
    for asset_name in assets or []:
        write_asset(assets_dir / asset_name)
    return case_dir


def publish_case(base_output_dir, folder_name, client=None, author='Offline Tester'):
    uploader = WeChatPublisher('fake-app-id', 'fake-secret')
    fake_client = client or FakeWeChatClient()
    uploader.client = fake_client
    ok = uploader.publish_draft(
        folder_name,
        author,
        base_output_dir=str(base_output_dir),
        theme='black_gold',
    )
    return ok, uploader, fake_client


def uploadable_assets(case_dir):
    assets_dir = case_dir / 'assets'
    if not assets_dir.exists():
        return []
    return sorted(
        path for path in assets_dir.glob('*')
        if path.is_file() and path.suffix.lower() in {'.png', '.jpg', '.gif'}
    )


def assert_success_case(root):
    folder_name = 'offline_success'
    markdown = (
        '# Offline Success\n\n'
        '正文 **加粗** <script>alert(1)</script>\n\n'
        '![](assets/HEADER_demo.png)\n\n'
        '![](assets/body_demo.gif)\n\n'
        '![](assets/ignored.svg)\n'
    )
    case_dir = make_case(
        root,
        folder_name,
        markdown=markdown,
        assets=['COVER_demo.png', 'HEADER_demo.png', 'body_demo.gif', 'ignored.svg'],
    )
    ok, _uploader, fake_client = publish_case(root, folder_name)

    article_data = fake_client.article_data or {}
    articles = article_data.get('articles') or []
    article = articles[0] if articles else {}
    content = article.get('content', '')
    checks = {
        'publish_draft_returned_true': ok is True,
        'uploaded_asset_count_matches': len(fake_client.uploaded) == len(uploadable_assets(case_dir)),
        'article_data_has_one_article': len(articles) == 1,
        'article_has_title': article.get('title') == folder_name,
        'article_has_author': article.get('author') == 'Offline Tester',
        'article_content_non_empty': len(content) > 100,
        'article_content_has_wrapper': content.startswith('<div style='),
        'article_content_has_no_script_tag': '<script' not in content.lower(),
        'article_content_has_uploaded_image_url': 'https://fake.local/HEADER_demo.png' in content,
        'thumb_media_id_set': article.get('thumb_media_id') == 'fake-thumb-media-id',
        'draft_submit_called': fake_client.article_data is not None,
    }
    return {
        'case': 'success_with_assets',
        'target_final_md': str(case_dir / f'FINAL_{folder_name}.md'),
        'uploaded': [
            {'file': os.path.basename(path), 'is_thumb': is_thumb}
            for path, is_thumb in fake_client.uploaded
        ],
        'checks': checks,
    }


def assert_missing_final_case(root):
    folder_name = 'missing_final'
    make_case(root, folder_name, markdown=None, assets=['COVER_demo.png'])
    ok, uploader, fake_client = publish_case(root, folder_name)
    checks = {
        'publish_draft_returned_false': ok is False,
        'reported_missing_final': '找不到已生成的公众号草稿文件' in uploader.last_error,
        'did_not_request_token': fake_client.ensure_token_calls == 0,
        'did_not_upload_assets': len(fake_client.uploaded) == 0,
        'did_not_submit_draft': fake_client.article_data is None,
    }
    return {
        'case': 'missing_final_markdown',
        'last_error': uploader.last_error,
        'checks': checks,
    }


def assert_empty_credentials_case():
    client = WeChatClient('', '')
    token = client.ensure_token()
    checks = {
        'ensure_token_returned_none': token is None,
        'reported_empty_credentials': 'AppID 或 AppSecret 为空' in client.last_error,
    }
    return {
        'case': 'empty_credentials',
        'last_error': client.last_error,
        'checks': checks,
    }


def assert_missing_cover_case(root):
    folder_name = 'missing_cover'
    markdown = '# Missing Cover\n\n正文\n\n![](assets/body.png)\n'
    make_case(root, folder_name, markdown=markdown, assets=['body.png'])
    ok, _uploader, fake_client = publish_case(root, folder_name)
    article = (fake_client.article_data or {}).get('articles', [{}])[0]
    checks = {
        'publish_still_succeeds': ok is True,
        'thumb_media_id_empty': article.get('thumb_media_id') == '',
        'draft_submit_called': fake_client.article_data is not None,
        'body_asset_uploaded': any(os.path.basename(path) == 'body.png' for path, _ in fake_client.uploaded),
    }
    return {
        'case': 'missing_cover',
        'uploaded': [
            {'file': os.path.basename(path), 'is_thumb': is_thumb}
            for path, is_thumb in fake_client.uploaded
        ],
        'checks': checks,
    }


def assert_missing_body_asset_case(root):
    folder_name = 'missing_body_asset'
    markdown = '# Missing Body Asset\n\n正文\n\n![](assets/not-found.png)\n'
    make_case(root, folder_name, markdown=markdown, assets=['COVER_demo.png'])
    ok, _uploader, fake_client = publish_case(root, folder_name)
    article = (fake_client.article_data or {}).get('articles', [{}])[0]
    content = article.get('content', '')
    checks = {
        'publish_still_succeeds': ok is True,
        'missing_image_not_rendered': 'not-found.png' not in content,
        'cover_uploaded': any(is_thumb for _path, is_thumb in fake_client.uploaded),
        'draft_submit_called': fake_client.article_data is not None,
    }
    return {
        'case': 'missing_body_asset',
        'content_length': len(content),
        'checks': checks,
    }


def assert_invalid_image_path_case(root):
    folder_name = 'invalid_image_path'
    markdown = '# Invalid Image Path\n\n正文\n\n![](../secret.png)\n\n![](https://example.com/x.png)\n'
    make_case(root, folder_name, markdown=markdown, assets=['COVER_demo.png'])
    ok, _uploader, fake_client = publish_case(root, folder_name)
    article = (fake_client.article_data or {}).get('articles', [{}])[0]
    content = article.get('content', '')
    checks = {
        'publish_still_succeeds': ok is True,
        'relative_escape_not_rendered': '../secret.png' not in content,
        'remote_image_not_rendered_without_upload': 'example.com/x.png' not in content,
        'draft_submit_called': fake_client.article_data is not None,
    }
    return {
        'case': 'invalid_image_path',
        'content_length': len(content),
        'checks': checks,
    }


def assert_upload_token_failure_case(root):
    folder_name = 'token_failure'
    make_case(root, folder_name, markdown='# Token Failure\n\n正文\n', assets=['COVER_demo.png'])
    ok, uploader, fake_client = publish_case(root, folder_name, client=FakeWeChatClient(token=None))
    checks = {
        'publish_draft_returned_false': ok is False,
        'last_error_copied_from_client': uploader.last_error == 'fake token failure',
        'did_not_upload_assets': len(fake_client.uploaded) == 0,
        'did_not_submit_draft': fake_client.article_data is None,
    }
    return {
        'case': 'token_failure',
        'last_error': uploader.last_error,
        'checks': checks,
    }


def run_check():
    with tempfile.TemporaryDirectory(prefix='writer-studio-publisher-offline-') as temp_dir:
        root = Path(temp_dir)
        summaries = [
            assert_success_case(root),
            assert_missing_final_case(root),
            assert_empty_credentials_case(),
            assert_missing_cover_case(root),
            assert_missing_body_asset_case(root),
            assert_invalid_image_path_case(root),
            assert_upload_token_failure_case(root),
        ]

    print(json.dumps({'cases': summaries}, ensure_ascii=False, indent=2))

    failed = []
    for summary in summaries:
        failed.extend(
            f"{summary['case']}.{name}"
            for name, passed in summary['checks'].items()
            if not passed
        )
    if failed:
        raise AssertionError(f'Offline publisher check failed: {", ".join(failed)}')


if __name__ == '__main__':
    run_check()
