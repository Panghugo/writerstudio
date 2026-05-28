import json
import os
import shutil
import sys
import tempfile

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import app
import publisher
import web
from writer_studio.obsidian import load_markdown_file
from writer_studio.wechat_draft import build_article_data, upload_assets
from writer_studio.wechat_format import markdown_to_wechat_html


def assert_true(condition, message):
    if not condition:
        raise AssertionError(message)


def test_generator_escapes_preview_html():
    input_dir = tempfile.mkdtemp(prefix="writer-studio-in-")
    output_dir = tempfile.mkdtemp(prefix="writer-studio-out-")
    try:
        with open(os.path.join(input_dir, "article.md"), "w", encoding="utf-8") as f:
            f.write("# 标题 <script>alert(1)</script>\n\n正文 **重点** <b>x</b>\n")

        app.main(
            target_md="article.md",
            input_dir=input_dir,
            output_dir=output_dir,
            theme="black_gold",
            author_name="Smoke",
        )

        preview_path = os.path.join(output_dir, "article", "PREVIEW_article.html")
        with open(preview_path, "r", encoding="utf-8") as f:
            preview = f.read()

        assert_true("&lt;script&gt;" in preview, "script tag should be escaped")
        assert_true("&lt;b&gt;x&lt;/b&gt;" in preview, "HTML body tag should be escaped")
        assert_true("<script>alert(1)</script>" not in preview, "raw script tag leaked into preview")
    finally:
        shutil.rmtree(input_dir, ignore_errors=True)
        shutil.rmtree(output_dir, ignore_errors=True)


def test_api_sanitizes_filename_and_generates_preview():
    client = web.app_server.test_client()
    session_id = "smoke-session"
    response = client.post(
        "/api/save_and_generate",
        data=json.dumps({
            "filename": "../坏:名字<script>",
            "session_id": session_id,
            "theme": "not-a-theme",
            "author_name": "Smoke",
            "content": "# 标题\n\n正文",
        }),
        content_type="application/json",
    )
    payload = response.get_json()
    assert_true(response.status_code == 200, f"unexpected status: {response.status_code}")
    assert_true(payload["status"] == "success", f"generation failed: {payload}")
    assert_true(".." not in payload["preview_url"], "preview URL should not contain traversal")
    assert_true("%E5%9D%8F_%E5%90%8D%E5%AD%97_script_" in payload["preview_url"], "sanitized name missing")


def test_obsidian_loader_copies_local_images_and_blocks_traversal():
    vault_dir = tempfile.mkdtemp(prefix="writer-studio-vault-")
    input_dir = tempfile.mkdtemp(prefix="writer-studio-obsidian-in-")
    try:
        with open(os.path.join(vault_dir, "note.md"), "w", encoding="utf-8") as f:
            f.write("# Note\n\n![[cover.png]]\n\n![remote](https://example.com/page)")
        with open(os.path.join(vault_dir, "cover.png"), "wb") as f:
            f.write(b"png")

        content, title = load_markdown_file("note.md", vault_dir, input_dir)

        assert_true(title == "note", "base filename should be returned")
        assert_true("![cover](cover.png)" in content, "Obsidian image should be rewritten")
        assert_true(os.path.exists(os.path.join(input_dir, "cover.png")), "local image should be copied")

        try:
            load_markdown_file("../note.md", vault_dir, input_dir)
        except ValueError:
            pass
        else:
            raise AssertionError("path traversal should be rejected")
    finally:
        shutil.rmtree(vault_dir, ignore_errors=True)
        shutil.rmtree(input_dir, ignore_errors=True)


def test_publisher_reports_missing_generated_draft_before_network():
    output_dir = tempfile.mkdtemp(prefix="writer-studio-publish-out-")
    try:
        uploader = publisher.WeChatPublisher("app-id", "app-secret")
        ok = uploader.publish_draft("missing", "Smoke", base_output_dir=output_dir)

        assert_true(not ok, "publish should fail when generated draft is missing")
        assert_true("找不到已生成的公众号草稿文件" in uploader.last_error, "missing draft reason should be visible")
    finally:
        shutil.rmtree(output_dir, ignore_errors=True)


def test_wechat_format_escapes_content_and_renders_images():
    html = markdown_to_wechat_html(
        "# 标题 <script>alert(1)</script>\n\n正文 **重点** <b>x</b>\n\n> 引用\n\n![](assets/H_1.png)",
        {"assets/H_1.png": "https://example.com/h.png?x=<bad>"},
        theme="black_gold",
    )

    assert_true("<script>" not in html.lower(), "wechat html should escape script tags")
    assert_true("&lt;script&gt;" in html, "escaped script text should remain visible")
    assert_true("&lt;b&gt;x&lt;/b&gt;" in html, "inline HTML should be escaped")
    assert_true("font-weight: bold;" in html, "bold markdown should render as styled span")
    assert_true("https://example.com/h.png?x=&lt;bad&gt;" in html, "image URL should be escaped")
    assert_true("<blockquote" in html, "blockquote should be rendered")


def test_wechat_draft_uploads_assets_and_builds_article_data():
    assets_dir = tempfile.mkdtemp(prefix="writer-studio-assets-")
    uploaded = []
    try:
        for filename in ["COVER_1.png", "HEADER_1.png", "H_1.gif", "skip.txt"]:
            with open(os.path.join(assets_dir, filename), "wb") as f:
                f.write(b"asset")

        def fake_upload(path, is_thumb=False):
            uploaded.append((os.path.basename(path), is_thumb))
            if is_thumb:
                return "thumb-media-id"
            return "https://fake.local/" + os.path.basename(path)

        assets_map, thumb_media_id = upload_assets(assets_dir, fake_upload)
        article_data = build_article_data(
            "article-name",
            "Smoke",
            "导语 **重点**\n\n![](assets/HEADER_1.png)",
            assets_map,
            thumb_media_id,
        )
        article = article_data["articles"][0]

        assert_true(("COVER_1.png", True) in uploaded, "cover should upload as thumb")
        assert_true(("HEADER_1.png", False) in uploaded, "header should upload as body image")
        assert_true(("H_1.gif", False) in uploaded, "gif should upload as body image")
        assert_true(("skip.txt", False) not in uploaded, "non-image assets should be skipped")
        assert_true(assets_map["assets/HEADER_1.png"].endswith("HEADER_1.png"), "body image map missing")
        assert_true(thumb_media_id == "thumb-media-id", "thumb media id missing")
        assert_true(article["title"] == "article-name", "article title mismatch")
        assert_true(article["author"] == "Smoke", "article author mismatch")
        assert_true(article["thumb_media_id"] == "thumb-media-id", "article thumb mismatch")
        assert_true("https://fake.local/HEADER_1.png" in article["content"], "article content image missing")
    finally:
        shutil.rmtree(assets_dir, ignore_errors=True)


if __name__ == "__main__":
    test_generator_escapes_preview_html()
    test_api_sanitizes_filename_and_generates_preview()
    test_obsidian_loader_copies_local_images_and_blocks_traversal()
    test_publisher_reports_missing_generated_draft_before_network()
    test_wechat_format_escapes_content_and_renders_images()
    test_wechat_draft_uploads_assets_and_builds_article_data()
    print("smoke-ok")
