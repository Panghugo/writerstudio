import html
import os
import re
import time


def export_html_preview(md_lines, output_dir, folder_name, main_title, style):
    print(f"   ⚡ 正在生成双模预览: {main_title}...")

    def render_inline(text):
        escaped = html.escape(text, quote=False)
        return re.sub(r'\*\*(.+?)\*\*', r'<span class="bold-text">\1</span>', escaped)

    try:
        accent_color = style.get('q_accent_color', style.get('cover_accent_color', '#E6C35C'))
        html_content = []
        html_content.append(f"""<!DOCTYPE html>
<html>
<head>
    <meta charset='utf-8'>
    <title>{html.escape(main_title)}</title>
    <style>
        body {{ font-family: 'PingFang SC', 'Microsoft YaHei', sans-serif; background: #f5f5f5; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; background: white; }}
        p {{ line-height: 1.8; color: #333; margin-bottom: 20px; }}
        .bold-text {{ color: {accent_color}; font-weight: bold; }}
        blockquote {{ border-left: 4px solid {accent_color}; margin: 20px 0; padding: 10px 15px; background: #f9f9f9; color: #666; font-size: 15px; border-radius: 4px; }}
        img {{ width: 100%; margin: 20px 0; display: block; }}
    </style>
</head>
<body>
<div class='container'>
""")

        cache_buster = int(time.time() * 1000)

        for line in md_lines:
            line = line.strip()
            if not line:
                continue

            if line.startswith("!["):
                match = re.search(r'\((.*?)\)', line)
                if match:
                    img_path = match.group(1)
                    img_url = f"{img_path}?t={cache_buster}"
                    html_content.append(f'<img src="{html.escape(img_url, quote=True)}" alt="图片" />')
            elif line.startswith("> "):
                clean_line = line.replace("> ", "", 1)
                processed_line = render_inline(clean_line)
                html_content.append(f'<blockquote>{processed_line}</blockquote>')
            else:
                processed_line = render_inline(line)
                html_content.append(f'<p>{processed_line}</p>')

        html_content.append("</div></body></html>")
        html_path = os.path.join(output_dir, f"PREVIEW_{folder_name}.html")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write("\n".join(html_content))
    except Exception as e:
        print(f"❌ HTML 生成失败: {e}")
