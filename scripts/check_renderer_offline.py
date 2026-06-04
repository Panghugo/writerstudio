import os
import shutil
import sys
import tempfile

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from PIL import Image

import app
from writer_studio import renderer
from writer_studio.renderer import (
    _truetype_cached,
    get_rich_bbox,
    load_font,
    process_text_lines,
)


def assert_true(condition, message):
    if not condition:
        raise AssertionError(message)


def test_load_font_is_cached():
    app.set_style('black_gold', 'Renderer Tester')
    _truetype_cached.cache_clear()
    first = load_font(48)
    second = load_font(48)
    info = _truetype_cached.cache_info()

    assert_true(first is second, 'same path+size should return the cached font object')
    assert_true(info.hits >= 1, f'expected at least one cache hit, got {info}')


def test_process_text_lines_splits_on_pipe():
    assert_true(
        process_text_lines('第一行 | 第二行 | 第三行') == ['第一行', '第二行', '第三行'],
        'pipe-separated text should split into trimmed lines',
    )
    wrapped = process_text_lines('这是一段没有竖线的较长文本需要按宽度折行处理', max_chars=6)
    assert_true(len(wrapped) > 1, f'long text without pipe should wrap into multiple lines: {wrapped}')


def test_get_rich_bbox_ignores_bold_markers():
    font = load_font(40)
    plain = get_rich_bbox('重点内容', font)
    marked = get_rich_bbox('重点\x01内容', font)
    assert_true(plain == marked, f'bold markers should not change bbox: {plain} vs {marked}')


def test_draw_functions_produce_valid_images():
    app.set_style('black_gold', 'Renderer Tester')
    out_dir = tempfile.mkdtemp(prefix='ws-render-')
    try:
        cover = os.path.join(out_dir, 'cover.png')
        header = os.path.join(out_dir, 'header.png')
        gif = os.path.join(out_dir, 'heading.gif')
        quote = os.path.join(out_dir, 'quote.png')

        renderer.draw_cover('主标题 | 副标题', cover)
        renderer.draw_header('主标题 | 副标题', header, read_time_mins=3, asset_dir=out_dir)
        renderer.draw_heading_gif('小节标题 | 第二行', gif, 1)
        renderer.draw_quote('一句金句 | 第二行金句', quote)

        for path in [cover, header, gif, quote]:
            assert_true(os.path.exists(path), f'render output missing: {path}')
            with Image.open(path) as img:
                width, height = img.size
                assert_true(width > 0 and height > 0, f'invalid image size for {path}: {img.size}')
    finally:
        shutil.rmtree(out_dir, ignore_errors=True)


def run_check():
    tests = [
        test_load_font_is_cached,
        test_process_text_lines_splits_on_pipe,
        test_get_rich_bbox_ignores_bold_markers,
        test_draw_functions_produce_valid_images,
    ]
    for test in tests:
        test()
    print('renderer-offline-ok')


if __name__ == '__main__':
    run_check()
