import os
import re
import shutil
import sys
import tempfile
from pathlib import Path

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from PIL import Image

import app


def assert_true(condition, message):
    if not condition:
        raise AssertionError(message)


def generate(input_dir, output_dir, md_name, content):
    with open(os.path.join(input_dir, md_name), 'w', encoding='utf-8') as f:
        f.write(content)
    app.main(
        target_md=md_name,
        input_dir=input_dir,
        output_dir=output_dir,
        theme='black_gold',
        author_name='Pipeline Tester',
    )


def asset_names(output_dir, folder):
    assets_dir = Path(output_dir, folder, 'assets')
    if not assets_dir.exists():
        return []
    return sorted(p.name for p in assets_dir.iterdir() if p.is_file())


def read_final(output_dir, folder, md_name):
    return Path(output_dir, folder, f'FINAL_{md_name}').read_text(encoding='utf-8')


def test_block_markers_generate_expected_assets():
    input_dir = tempfile.mkdtemp(prefix='ws-pipe-in-')
    output_dir = tempfile.mkdtemp(prefix='ws-pipe-out-')
    try:
        content = (
            '# 主标题 | 副标题\n\n'
            '## 第一节\n\n'
            '正文段落一。\n\n'
            '## 第二节\n\n'
            '>> 一句金句\n\n'
            '普通结尾。\n'
        )
        generate(input_dir, output_dir, 'doc.md', content)
        names = asset_names(output_dir, 'doc')

        covers = [n for n in names if n.startswith('COVER_')]
        headers = [n for n in names if n.startswith('HEADER_')]
        gifs = [n for n in names if n.startswith('H_')]
        quotes = [n for n in names if n.startswith('Q_')]

        assert_true(len(covers) == 1, f'expected 1 cover, got {names}')
        assert_true(len(headers) == 1, f'expected 1 header, got {names}')
        assert_true(len(gifs) == 2, f'expected 2 heading gifs, got {names}')
        assert_true(len(quotes) == 1, f'expected 1 quote, got {names}')

        final = read_final(output_dir, 'doc', 'doc.md')
        assert_true(f'![](assets/{headers[0]})' in final, 'header image should be referenced in FINAL')
        assert_true(f'![](assets/{gifs[0]})' in final, 'heading gif should be referenced in FINAL')
        assert_true(f'![](assets/{quotes[0]})' in final, 'quote image should be referenced in FINAL')
        assert_true('普通结尾。' in final, 'plain text should be preserved in FINAL')
    finally:
        shutil.rmtree(input_dir, ignore_errors=True)
        shutil.rmtree(output_dir, ignore_errors=True)


def test_local_image_copied_and_rewritten():
    input_dir = tempfile.mkdtemp(prefix='ws-pipe-in-')
    output_dir = tempfile.mkdtemp(prefix='ws-pipe-out-')
    try:
        Image.new('RGB', (48, 48), '#808080').save(os.path.join(input_dir, 'pic.png'))
        generate(input_dir, output_dir, 'doc.md', '# 标题\n\n![](pic.png)\n\n正文\n')
        names = asset_names(output_dir, 'doc')
        imgs = [n for n in names if n.startswith('IMG_')]

        assert_true(len(imgs) == 1, f'expected 1 copied image, got {names}')
        assert_true(imgs[0].endswith('.png'), f'copied image should keep extension: {imgs[0]}')
        final = read_final(output_dir, 'doc', 'doc.md')
        assert_true(f'![](assets/{imgs[0]})' in final, 'copied image should be referenced in FINAL')
    finally:
        shutil.rmtree(input_dir, ignore_errors=True)
        shutil.rmtree(output_dir, ignore_errors=True)


def test_missing_image_line_kept_verbatim():
    input_dir = tempfile.mkdtemp(prefix='ws-pipe-in-')
    output_dir = tempfile.mkdtemp(prefix='ws-pipe-out-')
    try:
        generate(input_dir, output_dir, 'doc.md', '# 标题\n\n![](does-not-exist.png)\n')
        final = read_final(output_dir, 'doc', 'doc.md')
        names = asset_names(output_dir, 'doc')

        assert_true('![](does-not-exist.png)' in final, 'missing image line should be kept verbatim')
        assert_true(not any(n.startswith('IMG_') for n in names), 'no IMG asset should exist for a missing image')
    finally:
        shutil.rmtree(input_dir, ignore_errors=True)
        shutil.rmtree(output_dir, ignore_errors=True)


def test_asset_filenames_are_stamped_and_unique():
    input_dir = tempfile.mkdtemp(prefix='ws-pipe-in-')
    output_dir = tempfile.mkdtemp(prefix='ws-pipe-out-')
    try:
        generate(input_dir, output_dir, 'doc.md', '# A\n\n## B\n\n## C\n\n>> D\n')
        names = asset_names(output_dir, 'doc')
        pattern = re.compile(r'^(COVER|HEADER|H|Q)_\d+_\d+\.(png|gif)$')

        for name in names:
            assert_true(bool(pattern.match(name)), f'unexpected asset filename format: {name}')
        assert_true(len(names) == len(set(names)), f'asset filenames should be unique: {names}')
    finally:
        shutil.rmtree(input_dir, ignore_errors=True)
        shutil.rmtree(output_dir, ignore_errors=True)


def test_output_dir_is_rebuilt_each_run():
    input_dir = tempfile.mkdtemp(prefix='ws-pipe-in-')
    output_dir = tempfile.mkdtemp(prefix='ws-pipe-out-')
    try:
        generate(input_dir, output_dir, 'doc.md', '# A\n\n正文\n')
        stale = Path(output_dir, 'doc', 'STALE.txt')
        stale.write_text('old', encoding='utf-8')
        assert_true(stale.exists(), 'precondition: stale file should exist before regeneration')

        generate(input_dir, output_dir, 'doc.md', '# A2\n\n正文\n')
        assert_true(not stale.exists(), 'stale file should be removed when output dir is rebuilt')
    finally:
        shutil.rmtree(input_dir, ignore_errors=True)
        shutil.rmtree(output_dir, ignore_errors=True)


def run_check():
    tests = [
        test_block_markers_generate_expected_assets,
        test_local_image_copied_and_rewritten,
        test_missing_image_line_kept_verbatim,
        test_asset_filenames_are_stamped_and_unique,
        test_output_dir_is_rebuilt_each_run,
    ]
    for test in tests:
        test()
    print('pipeline-offline-ok')


if __name__ == '__main__':
    run_check()
