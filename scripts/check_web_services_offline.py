import os
import shutil
import sys
from pathlib import Path

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from PIL import Image

from writer_studio import web_services
from writer_studio.file_safety import get_session_paths, sanitize_session_id


class FakeUploadFile:
    def __init__(self, filename, content=b'fake image bytes'):
        self.filename = filename
        self.content = content
        self.saved_path = None

    def save(self, path):
        self.saved_path = path
        with open(path, 'wb') as f:
            f.write(self.content)


def assert_true(condition, message):
    if not condition:
        raise AssertionError(message)


def cleanup_session(session_id):
    safe_id = sanitize_session_id(session_id)
    if not safe_id:
        return
    session_root = Path(ROOT_DIR, 'temp_sessions', safe_id)
    shutil.rmtree(session_root, ignore_errors=True)


def test_normalize_theme():
    assert_true(web_services.normalize_theme('tech_blue') == 'tech_blue', 'valid theme should pass through')
    assert_true(web_services.normalize_theme('  paper_white  ') == 'paper_white', 'theme should be stripped')
    assert_true(web_services.normalize_theme('bad-theme') == 'black_gold', 'invalid theme should fall back')
    assert_true(web_services.normalize_theme(None) == 'black_gold', 'missing theme should fall back')


def test_generate_preview_sanitizes_and_writes_session_files():
    session_id = 'web-services-offline-preview'
    cleanup_session(session_id)
    try:
        result = web_services.generate_preview({
            'filename': '../坏:名字<script>',
            'session_id': session_id,
            'theme': 'not-a-theme',
            'author_name': 'Service Tester',
            'content': '# 标题 <script>alert(1)</script>\n\n正文 **重点**',
        })
        input_dir, output_dir = get_session_paths(session_id)
        sanitized = '坏_名字_script_'
        md_path = Path(input_dir, f'{sanitized}.md')
        preview_dir = Path(output_dir, sanitized)

        assert_true(result['status'] == 'success', f'preview generation failed: {result}')
        assert_true('..' not in result['preview_url'], 'preview URL should not contain traversal')
        assert_true('%E5%9D%8F_%E5%90%8D%E5%AD%97_script_' in result['preview_url'], 'sanitized filename missing')
        assert_true(result['output_type'] == 'wechat_article', 'preview output type missing')
        assert_true(result['artifacts'][0]['type'] == 'html', 'preview artifact should be html')
        assert_true(result['artifacts'][0]['url'] == result['preview_url'], 'preview artifact URL mismatch')
        assert_true(md_path.exists(), 'sanitized markdown input should be written')
        assert_true(preview_dir.exists(), 'preview output folder should exist')
        assert_true(any(path.name.startswith('PREVIEW_') for path in preview_dir.iterdir()), 'preview html should exist')
    finally:
        cleanup_session(session_id)


def test_generate_social_image_returns_artifacts():
    session_id = 'web-services-offline-social'
    cleanup_session(session_id)
    try:
        input_dir, _ = get_session_paths(session_id)
        Path(input_dir).mkdir(parents=True, exist_ok=True)
        Image.new('RGB', (900, 520), '#dce5dc').save(Path(input_dir, 'demo.png'))
        paragraph = (
            '梁泽祖把车停下，打开 OPPO 手机，开始理解那些用手机的人。'
            '这是一段用于测试小红书文字图分页的正文。'
        )
        result = web_services.generate_social_image({
            'filename': 'social article',
            'session_id': session_id,
            'theme': 'editorial_card',
            'author_name': 'Service Tester',
            'social_brand_name': '有限理性',
            'social_brand_en': 'BOUNDED RATIONALITY',
            'social_brand_accent_text': '理性',
            'social_preset': 'image_first',
            'social_layout_overrides': {
                '0': {
                    'layout': 'wide',
                    'size': 'medium',
                    'show_caption': True,
                    'zoom': 125,
                    'crop_x': 20,
                    'crop_y': -10,
                    'margin_top': 24,
                    'margin_bottom': 16,
                }
            },
            'social_block_controls': {
                '1': {'order': 0, 'page_break_before': True, 'keep_with_next': True},
                '0': {'order': 1},
            },
            'content': '# 标题\n\n' + '\n\n'.join([paragraph] * 5) + '\n\n![广州街边的观察样图](demo.png)\n\n' + '\n\n'.join([paragraph] * 13),
        })
        _, output_dir = get_session_paths(session_id)
        assets_dir = Path(output_dir, 'social article', 'assets')

        assert_true(result['status'] == 'success', f'social generation failed: {result}')
        assert_true(result['output_type'] == 'social_cards', 'social output type missing')
        assert_true(result['page_count'] == len(result['image_urls']), 'page count should match image URLs')
        image_artifacts = [artifact for artifact in result['artifacts'] if artifact['type'] == 'image']
        zip_artifacts = [artifact for artifact in result['artifacts'] if artifact['type'] == 'zip']
        assert_true(len(image_artifacts) == len(result['image_urls']), 'image artifact count should match image URLs')
        assert_true(len(zip_artifacts) == 1, 'social zip artifact missing')
        assert_true(result['zip_url'] == zip_artifacts[0]['url'], 'zip URL should match zip artifact')
        assert_true(Path(output_dir, 'social article', zip_artifacts[0]['filename']).exists(), 'zip file should exist')
        assert_true(isinstance(result['quality_checks'], list), 'quality checks should be returned')
        assert_true(isinstance(result['page_layout'], list), 'page layout should be returned')
        assert_true(result['page_layout'], 'page layout should not be empty')
        assert_true(result['social_preset'] == 'image_first', 'social preset should be returned')
        assert_true(image_artifacts[0]['type'] == 'image', 'social artifact should be image')
        for artifact in image_artifacts:
            image_path = Path(assets_dir, artifact['filename'])
            assert_true(image_path.exists(), f'artifact file missing: {artifact}')
            with Image.open(image_path) as generated:
                assert_true(generated.size == (1080, 1440), f'social card size mismatch: {generated.size}')
    finally:
        cleanup_session(session_id)


def test_upload_content_image():
    session_id = 'web-services-offline-upload'
    cleanup_session(session_id)
    try:
        uploaded = FakeUploadFile('../bad:name.PNG')
        filename = web_services.save_uploaded_image(uploaded, session_id)
        input_dir, _ = get_session_paths(session_id)
        saved_path = Path(input_dir, filename)

        assert_true(filename.startswith('bad_name_'), 'uploaded filename should be sanitized')
        assert_true(filename.endswith('.png'), 'uploaded extension should normalize to lowercase')
        assert_true(saved_path.exists(), 'uploaded image should be saved')
        assert_true(Path(uploaded.saved_path) == saved_path, 'file.save should receive safe target path')

        try:
            web_services.save_uploaded_image(FakeUploadFile('notes.txt'), session_id)
        except ValueError as e:
            assert_true('Unsupported image type' in str(e), 'unsupported upload should explain failure')
        else:
            raise AssertionError('unsupported upload should fail')
    finally:
        cleanup_session(session_id)


def test_upload_feature_image_replaces_old_feature():
    session_id = 'web-services-offline-feature'
    cleanup_session(session_id)
    try:
        first = FakeUploadFile('cover.jpg', b'first')
        second = FakeUploadFile('cover.gif', b'second')

        first_name = web_services.save_uploaded_image(first, session_id, is_feature=True)
        second_name = web_services.save_uploaded_image(second, session_id, is_feature=True)
        input_dir, _ = get_session_paths(session_id)

        assert_true(first_name == 'feature.jpg', 'jpg feature name mismatch')
        assert_true(second_name == 'feature.png', 'unsupported feature extension should fall back to png')
        assert_true(not Path(input_dir, 'feature.jpg').exists(), 'old feature jpg should be removed')
        assert_true(Path(input_dir, 'feature.png').read_bytes() == b'second', 'new feature should be saved')
    finally:
        cleanup_session(session_id)


def test_remove_feature_image():
    session_id = 'web-services-offline-remove-feature'
    cleanup_session(session_id)
    try:
        web_services.save_uploaded_image(FakeUploadFile('cover.jpg', b'feature'), session_id, is_feature=True)
        result = web_services.remove_feature_image({'session_id': session_id})
        input_dir, _ = get_session_paths(session_id)

        assert_true(result['status'] == 'success', 'remove feature should succeed')
        assert_true(result['removed'] == ['feature.jpg'], 'removed feature filename mismatch')
        assert_true(not Path(input_dir, 'feature.jpg').exists(), 'feature image should be deleted')
    finally:
        cleanup_session(session_id)


def test_obsidian_missing_config_is_reported():
    original_loader = web_services.load_server_config
    try:
        web_services.load_server_config = lambda: {}
        try:
            web_services.get_obsidian_vault_path()
        except FileNotFoundError as e:
            assert_true('配置文件不存在' in str(e), 'missing config message mismatch')
        else:
            raise AssertionError('missing config should fail')

        web_services.load_server_config = lambda: {'obsidian_vault_path': '/definitely/not/a/vault'}
        try:
            web_services.get_obsidian_vault_path()
        except FileNotFoundError as e:
            assert_true('Obsidian 文件夹路径未配置或不存在' in str(e), 'missing vault message mismatch')
        else:
            raise AssertionError('missing vault should fail')
    finally:
        web_services.load_server_config = original_loader


def run_check():
    tests = [
        test_normalize_theme,
        test_generate_preview_sanitizes_and_writes_session_files,
        test_generate_social_image_returns_artifacts,
        test_upload_content_image,
        test_upload_feature_image_replaces_old_feature,
        test_remove_feature_image,
        test_obsidian_missing_config_is_reported,
    ]
    for test in tests:
        test()
    print('web-services-offline-ok')


if __name__ == '__main__':
    run_check()
