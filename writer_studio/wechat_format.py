import html as html_utils
import re


STYLE_CONFIG = {
    "p": "margin-bottom: 32px; font-size: 16px;",
    "img_card": "display: block; width: 100% !important; margin: 30px 0; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.08);",
    "img_header": "display: block; width: 100% !important; margin: 0 0 5px 0; pointer-events: none;",
    "img_heading": "display: block; width: 100% !important; margin: 10px 0; pointer-events: none;",
    "img_footer": "display: block; width: 100% !important; margin: 50px 0 0 0; pointer-events: none;",
}


def markdown_to_wechat_html(md_content, assets_map, theme="black_gold"):
    accent_color, body_font, lead_bg = theme_tokens(theme)
    body_style = (
        f"font-family: {body_font}; text-align: justify; line-height: 1.8; "
        "color: #333; padding: 20px 8px; letter-spacing: 0.034em;"
    )

    html = ""
    is_first_text_paragraph = True

    for raw_line in md_content.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        if line.startswith("![]"):
            html += render_image(line, assets_map)
            continue

        is_standard_quote = line.startswith("> ")
        clean_text = line.replace("# ", "").replace("## ", "").replace("> ", "")
        if not clean_text:
            continue

        clean_text = process_bold_text(clean_text, accent_color)

        if is_first_text_paragraph:
            print(f"   ✨ 识别到导语: {clean_text[:10]}...")
            html += render_lead_paragraph(clean_text, accent_color, lead_bg)
            is_first_text_paragraph = False
        elif is_standard_quote:
            html += render_quote(clean_text, accent_color, lead_bg)
        else:
            html += f'<p style="{STYLE_CONFIG["p"]}">{clean_text}</p>'

    return f'<div style="{body_style}">{html}</div>'


def theme_tokens(theme):
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
    pattern = r'\*\*(.+?)\*\*'
    replacement = fr'<span style="color: {accent_color}; font-weight: bold;">\1</span>'
    return re.sub(pattern, replacement, html_utils.escape(text, quote=False))


def render_image(line, assets_map):
    match = re.search(r'\((.*?)\)', line)
    if not match:
        return ""

    local_path = match.group(1)
    wechat_url = assets_map.get(local_path)
    if not wechat_url:
        return ""

    style = STYLE_CONFIG["img_card"]
    if "HEADER" in local_path:
        style = STYLE_CONFIG["img_header"]
    elif "FOOTER" in local_path:
        style = STYLE_CONFIG["img_footer"]
    elif "H_" in local_path:
        style = STYLE_CONFIG["img_heading"]

    return f'<img src="{html_utils.escape(wechat_url, quote=True)}" style="{style}" />'


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


def render_quote(clean_text, accent_color, lead_bg):
    return (
        f'<blockquote style="border-left: 4px solid {accent_color}; margin: 20px 0; '
        f'padding: 10px 15px; color: #666; font-size: 15px; background-color: {lead_bg}; '
        f'border-radius: 4px;">{clean_text}</blockquote>'
    )
