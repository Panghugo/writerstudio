import math
import os
import textwrap
from datetime import datetime
from functools import lru_cache

from PIL import Image, ImageDraw, ImageFont

import path_utils
from .renderers.social_cards import draw_social_text_images as render_social_text_images
from .themes import build_style
from .typography import auto_format_text, strip_markers


STYLE = build_style()
SPECIFIC_FEATURE_NAME = None


def set_style(style):
    global STYLE
    STYLE = style


def set_specific_feature(filename):
    global SPECIFIC_FEATURE_NAME
    SPECIFIC_FEATURE_NAME = filename


def get_font_path():
    base = path_utils.get_internal_path(os.path.join("fonts", STYLE["font_name"]))
    for ext in [".otf", ".ttf", ".ttc"]:
        if os.path.exists(base + ext):
            return base + ext
    print(f"⚠️ Font not found at: {base}")
    return None


@lru_cache(maxsize=128)
def _truetype_cached(path, size):
    return ImageFont.truetype(path, size)


def load_font(size):
    path = get_font_path()
    if not path:
        return ImageFont.load_default()
    return _truetype_cached(path, size)


def process_text_lines(text, max_chars=15):
    if "|" in text:
        return [line.strip() for line in text.split("|") if line.strip()]
    return textwrap.wrap(text, width=max_chars)


def add_film_grain(img, intensity=0.08):
    if img.mode != 'RGB':
        img = img.convert('RGB')
    width, height = img.size
    noise = Image.effect_noise((width, height), (intensity - 0.02) * 255).convert('RGB')
    return Image.blend(img, noise, 0.03)


def draw_rich_text(draw, x, y, text_with_markers, font, base_color, accent_color, init_bold=False):
    parts = text_with_markers.split('\x01')
    current_x = x
    is_bold = init_bold
    for i, part in enumerate(parts):
        if part:
            color = accent_color if is_bold else base_color
            draw.text((current_x, y), part, font=font, fill=color)
            current_x += font.getlength(part)
        if i < len(parts) - 1:
            is_bold = not is_bold
    return is_bold


def get_rich_bbox(text, font):
    return font.getbbox(strip_markers(text))


def draw_cover(text, save_path):
    text = text.replace('**', '\x01')
    w, h = STYLE["canvas_width"], int(STYLE["canvas_width"] / STYLE["cover_ratio"])
    img = Image.new("RGB", (w, h), STYLE["cover_bg_color"])
    draw = ImageDraw.Draw(img)
    main_title = text.split('|')[0].strip()
    margin = STYLE["cover_margin"]
    is_vintage = "cover_header_text" in STYLE

    if is_vintage:
        serif_bold_path = os.path.expanduser("~/Library/Fonts/SourceHanSerif-Bold.ttc")
        has_serif = os.path.exists(serif_bold_path)

        def load_serif(size):
            if has_serif:
                return ImageFont.truetype(serif_bold_path, size, index=0)
            return load_font(size)

        font_small = load_font(20)
        header_text = STYLE.get("cover_header_text", "")
        current_y = margin
        draw.text((margin, current_y), header_text, font=font_small, fill="#999990")
        current_y += 70

        parts = text.split('|', 1)
        main_title_text = parts[0].strip()
        sub_title = parts[1].strip() if len(parts) > 1 else ""

        max_width = w - (margin * 2)
        title_font_size = STYLE["cover_main_size"]
        sub_reserve = 100 if sub_title else 0
        footer_reserve = 80
        available_title_h = h - current_y - margin - sub_reserve - footer_reserve

        while title_font_size >= 70:
            font_main = load_serif(title_font_size)
            title_lines = []
            current_line = ""
            for ch in list(main_title_text):
                test = current_line + ch
                if font_main.getlength(test) > max_width and current_line:
                    title_lines.append(current_line)
                    current_line = ch
                else:
                    current_line = test
            if current_line:
                title_lines.append(current_line)

            line_height = int(title_font_size * 1.35)
            total_title_h = len(title_lines) * line_height
            if total_title_h <= available_title_h:
                break
            title_font_size -= 5

        bold_state = False
        for line in title_lines:
            bold_state = draw_rich_text(
                draw, margin, current_y, line,
                font=font_main,
                base_color=STYLE["cover_text_color"],
                accent_color=STYLE.get("cover_accent_color", STYLE["cover_text_color"]),
                init_bold=bold_state,
            )
            current_y += line_height

        if sub_title:
            current_y += 15
            sub_size = STYLE.get("cover_sub_size", 42)
            font_sub = load_serif(sub_size)
            draw.text((margin, current_y), sub_title, font=font_sub, fill="#555555")
            current_y += int(sub_size * 1.5)

        font_meta = load_font(STYLE["cover_footer_size"])
        meta_text = STYLE.get("cover_meta_text", STYLE['author_text'])
        line_y = h - margin - 50
        draw.line([(margin, line_y), (w - margin, line_y)], fill="#CCCCC0", width=1)
        draw.text((margin, line_y + 18), meta_text, font=font_meta, fill="#999990")
    else:
        current_y = margin + 20
        draw.rectangle([(margin, current_y), (margin + 80, current_y + 6)], fill=STYLE["cover_text_color"])
        current_y += 70
        max_width = w - (margin * 2)
        current_font_size = STYLE["cover_main_size"]
        min_font_size = 60
        font_main = load_font(current_font_size)
        while font_main.getlength(strip_markers(main_title)) > max_width and current_font_size > min_font_size:
            current_font_size -= 2
            font_main = load_font(current_font_size)
        draw_rich_text(
            draw, margin, current_y, main_title,
            font=font_main,
            base_color=STYLE["cover_text_color"],
            accent_color=STYLE.get("cover_accent_color", STYLE["cover_text_color"]),
        )
        font_footer = load_font(STYLE["cover_footer_size"])
        date_str = datetime.now().strftime("%b %d, %Y").upper()
        footer_text = f"{STYLE['author_text']}   ·   {date_str}"
        bbox = font_footer.getbbox(footer_text)
        f_x, f_y = w - margin - (bbox[2] - bbox[0]), h - margin - (bbox[3] - bbox[1])
        draw.line([(0, f_y - 40), (w, f_y - 40)], fill=STYLE["cover_text_color"], width=1)
        draw.text((f_x, f_y), footer_text, font=font_footer, fill=STYLE["cover_text_color"])
    add_film_grain(img).save(save_path)


def draw_header(text, save_path, read_time_mins, asset_dir="input"):
    text = text.replace('**', '\x01')
    global SPECIFIC_FEATURE_NAME
    current_feature_name = SPECIFIC_FEATURE_NAME
    SPECIFIC_FEATURE_NAME = None
    w, h = STYLE["canvas_width"], int(STYLE["canvas_width"] / STYLE["header_ratio"])
    main_font_size, sub_font_size = STYLE["header_main_size"], STYLE["header_sub_size"]
    font_footer = load_font(STYLE["header_footer_size"])
    img = Image.new("RGB", (w, h), STYLE["header_bg_color"])
    draw = ImageDraw.Draw(img)
    margin = STYLE["header_margin"]
    max_width = w - (margin * 2)
    out_m = 40

    draw.rectangle([(out_m, out_m), (w - out_m, h - out_m)], outline=STYLE["header_text_color"], width=1)

    parts = text.split('|', 1)
    main_title = parts[0].strip()
    sub_title = parts[1].strip() if len(parts) > 1 else ""

    current_y = margin + 40
    draw.text((margin, current_y), "ISSUE / THE ARENA", font=font_footer, fill=STYLE["header_text_color"])
    current_y += 60

    font_main = load_font(main_font_size)
    while font_main.getlength(strip_markers(main_title)) > max_width and main_font_size > 40:
        main_font_size -= 2
        font_main = load_font(main_font_size)
    draw_rich_text(
        draw, margin, current_y, main_title,
        font=font_main,
        base_color=STYLE["header_text_color"],
        accent_color=STYLE.get("header_accent_color", STYLE["header_text_color"]),
    )
    bbox_main = get_rich_bbox(main_title, font_main)
    current_y += (bbox_main[3] - bbox_main[1]) + 40

    if sub_title:
        current_y += 10
        draw.rectangle([(margin, current_y), (margin + 60, current_y + 4)], fill=STYLE["header_text_color"])
        current_y += 30
        font_sub = load_font(sub_font_size)
        while font_sub.getlength(sub_title) > max_width and sub_font_size > 24:
            sub_font_size -= 2
            font_sub = load_font(sub_font_size)
        draw.text((margin, current_y), sub_title, font=font_sub, fill=STYLE["header_text_color"])
        bbox_sub = font_sub.getbbox(sub_title)
        current_y += (bbox_sub[3] - bbox_sub[1]) + 20

    text_end_y = current_y + 40
    bbox_samp = font_footer.getbbox("Tg")
    line_h = bbox_samp[3] - bbox_samp[1]
    y_line2 = h - margin - line_h
    y_line1 = y_line2 - line_h - 20
    footer_top_y = y_line1 - 20
    available_h, target_w = footer_top_y - text_end_y - 40, w - (margin * 2)

    feature_path = None
    if current_feature_name:
        path = os.path.join(asset_dir, current_feature_name)
        if os.path.exists(path):
            feature_path = path

    if not feature_path:
        for candidate in ["feature.png", "feature.jpg", "feature.jpeg"]:
            path = os.path.join(asset_dir, candidate)
            if os.path.exists(path):
                feature_path = path
                break

    if feature_path:
        try:
            feature_img = Image.open(feature_path).convert("RGBA")
            if available_h > 100:
                ratio = feature_img.width / feature_img.height
                new_h = int(target_w / ratio)
                if new_h > available_h:
                    new_h = available_h
                    target_w = int(new_h * ratio)
                    final_x = (w - target_w) // 2
                else:
                    final_x = margin
                feature_img = feature_img.resize((target_w, new_h), Image.LANCZOS)
                img.paste(feature_img, (final_x, text_end_y), feature_img)
        except Exception as e:
            print(f"⚠️ 特性图加载失败 ({feature_path}): {type(e).__name__}: {e}")
    elif available_h > 200:
        cx, cy, r = w // 2, text_end_y + (available_h // 2), 80
        draw.ellipse([(cx - r, cy - r), (cx + r, cy + r)], outline=STYLE["header_text_color"], width=1)
        draw.ellipse([(cx - r * 1.5, cy - r * 1.5), (cx + r * 1.5, cy + r * 1.5)], outline=STYLE["header_text_color"], width=1)
        draw.line([(cx, cy - r * 2), (cx, cy + r * 2)], fill=STYLE["header_text_color"], width=1)

    draw.text((margin, y_line1), STYLE['author_text'], font=font_footer, fill=STYLE["header_text_color"])
    draw.text((margin, y_line2), datetime.now().strftime("%B %d, %Y").upper(), font=font_footer, fill=STYLE["header_text_color"])
    read_text = f"预计阅读 {read_time_mins} 分钟"
    bbox_r = font_footer.getbbox(read_text)
    draw.text((w - margin - (bbox_r[2] - bbox_r[0]), y_line2), read_text, font=font_footer, fill=STYLE["header_text_color"])
    add_film_grain(img).save(save_path)


def draw_heading_gif(text, save_path, index):
    text = text.replace('**', '\x01')
    font, num_font = load_font(STYLE["h_font_size"]), load_font(STYLE["h_num_font_size"])
    w, cx = STYLE["canvas_width"], STYLE["canvas_width"] // 2
    lines = process_text_lines(text)
    line_bboxes = [get_rich_bbox(line, font) for line in lines]
    total_text_h = sum(bbox[3] - bbox[1] for bbox in line_bboxes) + (len(lines) * 25) - 25
    img_h = STYLE["h_padding_top"] + (STYLE["h_num_radius"] * 2) + STYLE["h_text_gap"] + total_text_h + STYLE["h_padding_bottom"]
    frames = []
    for f in range(STYLE["gif_frames"]):
        img = Image.new("RGB", (w, img_h), STYLE["h_bg_color"])
        draw = ImageDraw.Draw(img)
        offset = math.sin((f / STYLE["gif_frames"]) * math.pi) * 4
        cy, br = STYLE["h_padding_top"] + STYLE["h_num_radius"], STYLE["h_num_radius"]
        draw.line([(0, 20), (w, 20)], fill=STYLE["h_num_color"], width=4)
        draw.line([(0, 32), (w, 32)], fill=STYLE["h_num_color"], width=1)
        draw.ellipse([(cx - (br + offset), cy - (br + offset)), (cx + (br + offset), cy + (br + offset))], outline=STYLE["h_num_color"], width=1)
        draw.ellipse([(cx - (br - 6 + offset * 0.6), cy - (br - 6 + offset * 0.6)), (cx + (br - 6 + offset * 0.6), cy + (br - 6 + offset * 0.6))], outline=STYLE["h_num_color"], width=2)
        num_text = str(index)
        num_bbox = num_font.getbbox(num_text)
        draw.text((cx - (num_bbox[2] - num_bbox[0]) // 2, cy - (num_bbox[3] - num_bbox[1]) // 2 - num_bbox[1] - 2), num_text, font=num_font, fill=STYLE["h_num_color"])
        cy_t = cy + br + STYLE["h_text_gap"]
        for line, line_bbox in zip(lines, line_bboxes):
            draw_rich_text(
                draw, cx - (line_bbox[2] - line_bbox[0]) // 2, cy_t, line,
                font=font,
                base_color=STYLE["h_color"],
                accent_color=STYLE.get("h_num_color", STYLE["h_color"]),
            )
            cy_t += (line_bbox[3] - line_bbox[1]) + 25
        draw.line([(0, img_h - 20), (w, img_h - 20)], fill=STYLE["h_num_color"], width=4)
        frames.append(img)
    frames[0].save(save_path, save_all=True, append_images=frames[1:], duration=STYLE["gif_duration"], loop=0)


def draw_quote(text, save_path):
    text = text.replace('**', '\x01')
    font = load_font(STYLE["q_font_size"])
    w = STYLE["canvas_width"]
    qm_font = load_font(STYLE["q_font_size"] * 4)
    lines = process_text_lines(text, (w - STYLE["q_padding_x"] * 2) // STYLE["q_font_size"])
    line_bboxes = [get_rich_bbox(line, font) for line in lines]
    total_h = sum(bbox[3] - bbox[1] for bbox in line_bboxes) + (len(lines) * STYLE["q_line_spacing"]) - STYLE["q_line_spacing"]
    img_h = total_h + (STYLE["q_deco_gap"] * 2)
    mask = Image.new("L", (w, img_h), 0)
    draw_mask = ImageDraw.Draw(mask)
    r = STYLE["q_radius"]
    draw_mask.rounded_rectangle([(0, 0), (w, img_h)], radius=r, fill=255)
    fold_size = STYLE["q_fold_size"]
    cut_poly = [(w, img_h), (w, img_h - fold_size), (w - fold_size, img_h)]
    draw_mask.polygon(cut_poly, fill=0)
    card_color_layer = Image.new("RGBA", (w, img_h), STYLE["q_bg_color"])
    img = Image.new("RGBA", (w, img_h), (0, 0, 0, 0))
    img.paste(card_color_layer, mask=mask)
    draw = ImageDraw.Draw(img)
    watermark_color = (200, 200, 200, 60)
    draw.text((STYLE["q_padding_x"] - 40, STYLE["q_deco_gap"] - 40), "“", font=qm_font, fill=watermark_color)
    for y in [STYLE["q_deco_gap"] - 50, img_h - STYLE["q_deco_gap"] + 50]:
        draw.line([(w // 2 - STYLE["q_deco_width"], y), (w // 2 + STYLE["q_deco_width"], y)], fill=STYLE["q_line_color"], width=4)
        draw.regular_polygon((w // 2, y, 6), 4, rotation=0, fill=STYLE["q_line_color"])
    cy = (img_h - total_h) // 2
    bold_state = False
    for line, line_bbox in zip(lines, line_bboxes):
        lx = w - (line_bbox[2] - line_bbox[0]) - (STYLE["q_padding_x"] + 20) if line.startswith(("——", "--")) else (w - (line_bbox[2] - line_bbox[0])) // 2
        bold_state = draw_rich_text(
            draw, lx, cy, line,
            font=font,
            base_color=STYLE["q_text_color"],
            accent_color=STYLE.get("q_accent_color", STYLE.get("cover_accent_color", STYLE["q_text_color"])),
            init_bold=bold_state,
        )
        cy += (line_bbox[3] - line_bbox[1]) + STYLE["q_line_spacing"]
    flap_poly = [(w - fold_size, img_h - fold_size), (w, img_h - fold_size), (w - fold_size, img_h)]
    draw.polygon(flap_poly, fill="#F2F2F2", outline=None)
    draw.line([(w - fold_size, img_h), (w - fold_size, img_h - fold_size), (w, img_h - fold_size)], fill=STYLE["footer_gold"], width=1)
    draw.line([(w - fold_size, img_h), (w, img_h - fold_size)], fill="#E0E0E0", width=1)
    img.save(save_path, format="PNG")


def draw_social_text_image(title, paragraphs, save_path):
    page_paths = draw_social_text_images(
        title,
        paragraphs,
        os.path.dirname(save_path),
        os.path.splitext(os.path.basename(save_path))[0],
    )
    if page_paths and page_paths[0] != save_path:
        os.replace(page_paths[0], save_path)


def draw_social_text_images(title, paragraphs, output_dir, base_name):
    return render_social_text_images(title, paragraphs, output_dir, base_name, STYLE)
