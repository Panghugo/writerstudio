import html as html_utils
import os
import re
import time


STYLE_CONFIG = {
    "p": "margin-bottom: 32px; font-size: 16px;",
    "img_card": "display: block; width: 100% !important; margin: 30px 0; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.08);",
    "img_header": "display: block; width: 100% !important; margin: 0 0 5px 0; pointer-events: none;",
    "img_heading": "display: block; width: 100% !important; margin: 10px 0; pointer-events: none;",
    "img_footer": "display: block; width: 100% !important; margin: 50px 0 0 0; pointer-events: none;",
}


def markdown_to_wechat_html(md_content, assets_map=None, theme="black_gold", cache_buster=None):
    allow_local_images = assets_map is None
    assets_map = assets_map or {}
    accent_color, body_font, lead_bg = theme_tokens(theme)
    body_style = (
        f"font-family: {body_font}; text-align: justify; line-height: 1.8; "
        "color: #333; padding: 20px 8px; letter-spacing: 0.034em;"
    )
    if theme == "editorial_card":
        body_style = (
            f"font-family: {body_font}; text-align: justify; line-height: 1.9; "
            "color: #202020; padding: 22px 14px 8px; letter-spacing: 0.02em; "
            "background-color: #F4F4EF;"
        )

    rendered = []
    is_first_text_paragraph = True

    for raw_line in md_content.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        if line.startswith("!["):
            rendered.append(render_image(line, assets_map, cache_buster=cache_buster, allow_local=allow_local_images))
            continue

        is_standard_quote = line.startswith("> ")
        if line.startswith("## "):
            clean_text = line[3:].strip()
        elif line.startswith("# "):
            clean_text = line[2:].strip()
        elif is_standard_quote:
            clean_text = line[2:].strip()
        else:
            clean_text = line
        if not clean_text:
            continue

        clean_text = process_bold_text(clean_text, accent_color)

        if is_first_text_paragraph and theme != "editorial_card":
            rendered.append(render_lead_paragraph(clean_text, accent_color, lead_bg))
            is_first_text_paragraph = False
        elif is_standard_quote:
            rendered.append(render_quote(clean_text, accent_color, lead_bg, theme))
        else:
            rendered.append(render_paragraph(clean_text, theme))
            is_first_text_paragraph = False

    return f'<div style="{body_style}">{"".join(rendered)}</div>'


def render_preview_document(md_lines, output_dir, folder_name, main_title, style):
    print(f"   ⚡ 正在生成双模预览: {main_title}...")
    try:
        theme = style.get("theme_name", "black_gold") if style else "black_gold"
        if "social_bg_color" in (style or {}):
            theme = "editorial_card"
        cache_buster = int(time.time() * 1000)
        article_html = markdown_to_wechat_html(
            "\n".join(md_lines),
            assets_map=None,
            theme=theme,
            cache_buster=cache_buster,
        )

        page_bg = "#ececea" if theme == "editorial_card" else "#f5f5f5"
        container_bg = (style or {}).get("social_bg_color", "white") if theme == "editorial_card" else "white"
        container_padding = "0 34px 44px" if theme == "editorial_card" else "20px"
        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{html_utils.escape(main_title)}</title>
    <style>
        body {{ margin: 0; background: {page_bg}; }}
        .container {{
            max-width: 600px;
            margin: 0 auto;
            padding: {container_padding};
            background: {container_bg};
        }}
        img {{ max-width: 100%; }}
    </style>
</head>
<body>
    <div class="container">{article_html}</div>
</body>
</html>"""

        html_path = os.path.join(output_dir, f"PREVIEW_{folder_name}.html")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        return html_path
    except Exception as e:
        print(f"❌ HTML 生成失败: {e}")
        return None


def theme_tokens(theme):
    if theme == "editorial_card":
        return (
            "#8B5B3E",
            "'Source Han Sans SC', 'Noto Sans CJK SC', 'PingFang SC', sans-serif",
            "#F4F4EF",
        )
    if theme == "vintage_press":
        return (
            "#A52A2A",
            "'Source Han Serif SC', 'Noto Serif CJK SC', 'STSong', serif",
            "#F4F1EA",
        )
    return (
        "#E6C35C",
        "'Optima-Regular', 'Optima', 'PingFang SC', sans-serif",
        "#f9f9f9",
    )


def process_bold_text(text, accent_color):
    escaped = html_utils.escape(text, quote=False)
    return re.sub(
        r'\*\*(.+?)\*\*',
        fr'<span style="color: {accent_color}; font-weight: bold;">\1</span>',
        escaped,
    )


def render_image(line, assets_map, cache_buster=None, allow_local=False):
    match = re.search(r'\((.*?)\)', line)
    if not match:
        return ""

    local_path = match.group(1)
    image_url = assets_map.get(local_path)
    if not image_url:
        if not allow_local:
            return ""
        image_url = local_path
    if cache_buster and image_url == local_path:
        image_url = f"{image_url}?t={cache_buster}"

    style = STYLE_CONFIG["img_card"]
    if "HEADER" in local_path:
        style = STYLE_CONFIG["img_header"]
    elif "FOOTER" in local_path:
        style = STYLE_CONFIG["img_footer"]
    elif "H_" in local_path:
        style = STYLE_CONFIG["img_heading"]

    return f'<img src="{html_utils.escape(image_url, quote=True)}" style="{style}" />'


def render_lead_paragraph(clean_text, accent_color, lead_bg):
    separator_html = f"""
    <section style="margin: 15px auto 20px auto; text-align: center; line-height: 1;">
        <span style="display: inline-block; width: 40px; border-top: 1px solid {accent_color}; vertical-align: middle;"></span>
        <span style="display: inline-block; width: 6px; height: 6px; background-color: {accent_color}; border-radius: 50%; vertical-align: middle; margin: 0 8px;"></span>
        <span style="display: inline-block; width: 40px; border-top: 1px solid {accent_color}; vertical-align: middle;"></span>
    </section>
    """
    return (
        separator_html
        + f'<section style="font-size: 15px; color: #666; line-height: 1.7; text-align: justify; '
        + f'padding: 20px 16px 20px 24px; border-left: 4px solid {accent_color}; '
        + f'background-color: {lead_bg}; margin-bottom: 50px;">{clean_text}</section>'
    )


def render_paragraph(clean_text, theme):
    if theme == "editorial_card":
        return (
            '<p style="margin: 0 0 30px 0; font-size: 16px; line-height: 1.95; '
            'color: #202020; letter-spacing: 0.02em;">'
            f'{clean_text}</p>'
        )
    return f'<p style="{STYLE_CONFIG["p"]}">{clean_text}</p>'


def render_quote(clean_text, accent_color, lead_bg, theme="black_gold"):
    if theme == "editorial_card":
        return (
            f'<blockquote style="border-left: 3px solid {accent_color}; margin: 24px 0 30px 0; '
            'padding: 2px 0 2px 16px; color: #4A4A46; font-size: 15px; '
            'line-height: 1.85; background: transparent;">'
            f'{clean_text}</blockquote>'
        )
    return (
        f'<blockquote style="border-left: 4px solid {accent_color}; margin: 20px 0; '
        f'padding: 10px 15px; color: #666; font-size: 15px; background-color: {lead_bg}; '
        f'border-radius: 4px;">{clean_text}</blockquote>'
    )
