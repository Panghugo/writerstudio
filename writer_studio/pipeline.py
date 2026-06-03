import math
import os
import re
import shutil
import time

from .preview import export_html_preview
from .renderer import (
    auto_format_text,
    draw_cover,
    draw_header,
    draw_heading_gif,
    draw_quote,
)


def generate_articles(target_md=None, input_dir="input", output_dir="output", style=None):
    os.makedirs(input_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)

    # 资源文件名用行号(index)保证同次生成内唯一；run_stamp 仅用于区分不同生成批次，
    # 不再依赖 time.time() 的单调性来避免碰撞。
    run_stamp = int(time.time())

    if target_md:
        files = [target_md]
    else:
        files = [filename for filename in os.listdir(input_dir) if filename.endswith(".md")]

    if not files:
        return print(f"❌ {input_dir} 文件夹里没有 Markdown 文件！")

    for md_file in files:
        source_path = os.path.join(input_dir, md_file)
        if not os.path.exists(source_path):
            print(f"⚠️ 跳过不存在的文件: {md_file}")
            continue

        print(f"📄 处理中: {md_file}")
        with open(source_path, "r", encoding="utf-8") as f:
            full_text = f.read()

        read_time_mins = max(1, math.ceil(len(full_text) / 400))
        folder_name = os.path.splitext(md_file)[0]
        out_dir = os.path.join(output_dir, folder_name)
        assets_dir = os.path.join(out_dir, "assets")

        if os.path.exists(out_dir):
            shutil.rmtree(out_dir)
        os.makedirs(assets_dir)

        lines = full_text.splitlines()
        final_lines = []
        heading_count = 0
        main_title = "未命名文章"

        for index, raw_line in enumerate(lines):
            line = raw_line.strip()
            timestamp = f"{run_stamp}_{index}"

            if line.startswith("# "):
                title_text = auto_format_text(line.replace("# ", "").strip())
                main_title = title_text.split('|')[0]
                if title_text:
                    draw_cover(title_text, os.path.join(assets_dir, f"COVER_{timestamp}.png"))
                    header_name = f"HEADER_{timestamp}.png"
                    draw_header(title_text, os.path.join(assets_dir, header_name), read_time_mins, asset_dir=input_dir)
                    final_lines.append(f"![](assets/{header_name})\n\n")
            elif line.startswith("## "):
                heading_text = auto_format_text(line.replace("## ", "").strip())
                if heading_text:
                    heading_count += 1
                    draw_heading_gif(heading_text, os.path.join(assets_dir, f"H_{timestamp}.gif"), heading_count)
                    final_lines.append(f"\n![](assets/H_{timestamp}.gif)\n")
            elif line.startswith(">> "):
                quote_text = auto_format_text(line.replace(">> ", "").strip())
                if quote_text:
                    draw_quote(quote_text, os.path.join(assets_dir, f"Q_{timestamp}.png"))
                    final_lines.append(f"\n![](assets/Q_{timestamp}.png)\n")
            elif line.startswith("!["):
                _copy_markdown_image(line, input_dir, assets_dir, timestamp, final_lines)
            else:
                formatted_line = auto_format_text(line)
                final_lines.append(formatted_line + "\n" if formatted_line else "\n")

        with open(os.path.join(out_dir, "FINAL_" + md_file), "w", encoding="utf-8") as f:
            f.writelines(final_lines)

        export_html_preview(final_lines, out_dir, folder_name, main_title, style or {})


def _copy_markdown_image(line, input_dir, assets_dir, timestamp, final_lines):
    match = re.search(r'\((.*?)\)', line)
    if not match:
        return

    src_path = match.group(1)
    possible_paths = [
        src_path,
        os.path.join(input_dir, src_path),
        os.path.join(input_dir, os.path.basename(src_path)),
    ]

    for path in possible_paths:
        if os.path.exists(path) and os.path.isfile(path):
            ext = os.path.splitext(path)[1]
            new_name = f"IMG_{timestamp}{ext}"
            shutil.copy(path, os.path.join(assets_dir, new_name))
            final_lines.append(f"![](assets/{new_name})\n")
            return

    final_lines.append(line + "\n")
