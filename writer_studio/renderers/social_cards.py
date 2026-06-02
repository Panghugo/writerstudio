import os
import re
import time
from datetime import datetime

from PIL import Image, ImageDraw, ImageFont

import path_utils
from ..typography import auto_format_text, strip_markers, wrap_text_by_width


IMAGE_PATTERN = re.compile(r'^!\[(.*?)\]\((.*?)\)(?:\{([^}]*)\})?$')


def extract_social_image_text(content, layout_overrides=None, block_controls=None):
    title = ""
    blocks = []
    image_index = 0
    block_index = 0
    layout_overrides = layout_overrides or {}
    block_controls = block_controls or {}

    def add_block(block):
        nonlocal block_index
        control = block_controls.get(str(block_index), {})
        block["block_index"] = block_index
        block["page_break_before"] = bool(control.get("page_break_before"))
        block["keep_with_next"] = bool(control.get("keep_with_next"))
        block["order"] = control.get("order", block_index)
        blocks.append(block)
        block_index += 1

    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        image_match = IMAGE_PATTERN.match(line)
        if image_match:
            attrs = parse_image_attrs(image_match.group(3) or "")
            override = layout_overrides.get(str(image_index), {})
            add_block({
                "kind": "image",
                "alt": image_match.group(1).strip(),
                "src": image_match.group(2).strip(),
                "attrs": attrs,
                "image_index": image_index,
                "layout": override.get("layout") or attrs.get("layout") or attrs.get("variant") or "auto",
                "size": override.get("size") or attrs.get("size") or "auto",
                "show_caption": override.get("show_caption", attrs.get("caption", "show") != "hide"),
                "zoom": override.get("zoom", attrs.get("zoom", 100)),
                "crop_x": override.get("crop_x", attrs.get("crop_x", 0)),
                "crop_y": override.get("crop_y", attrs.get("crop_y", 0)),
                "margin_top": override.get("margin_top", attrs.get("margin_top", 0)),
                "margin_bottom": override.get("margin_bottom", attrs.get("margin_bottom", 0)),
            })
            image_index += 1
            continue
        if line.startswith("# "):
            title = auto_format_text(line.replace("# ", "", 1).strip()).split("|", 1)[0].strip()
            continue
        if line.startswith("## "):
            heading = auto_format_text(line.replace("## ", "", 1).strip())
            if heading:
                add_block({"kind": "heading", "text": heading})
            continue
        if line.startswith(">> "):
            line = line.replace(">> ", "", 1).strip()
        elif line.startswith("> "):
            line = line.replace("> ", "", 1).strip()
        line = re.sub(r'^[-*+]\s+', '', line)
        line = auto_format_text(line)
        if line:
            add_block({"kind": "body", "text": line})
    return title, sort_social_blocks(blocks)


def sort_social_blocks(blocks):
    return sorted(blocks, key=lambda block: (safe_order(block.get("order"), block.get("block_index", 0)), block.get("block_index", 0)))


def safe_order(value, fallback):
    try:
        return int(value)
    except (TypeError, ValueError):
        return fallback


def create_social_cards(content, output_dir, style, base_name=None, image_dirs=None, layout_overrides=None, block_controls=None, return_metadata=False):
    title, blocks = extract_social_image_text(content, layout_overrides=layout_overrides, block_controls=block_controls)
    if not blocks:
        raise ValueError("没有可生成文字图的正文内容")

    image_base_name = base_name or f"TEXT_CARD_{int(time.time() * 1000)}"
    return draw_social_text_images(title, blocks, output_dir, image_base_name, style, image_dirs=image_dirs, return_metadata=return_metadata)


def draw_social_text_images(title, blocks, output_dir, base_name, style, image_dirs=None, return_metadata=False):
    os.makedirs(output_dir, exist_ok=True)
    font_body = load_social_font(style, style.get("social_font_size", 36), "normal")
    font_heading = load_social_font(style, style.get("social_heading_size", 36), "medium")
    font_caption = load_social_font(style, style.get("social_caption_size", 20), "regular")
    font_brand = load_social_font(style, style.get("social_brand_size", 34), "medium")
    font_brand_en = load_social_font(style, style.get("social_brand_en_size", 15), "regular")
    font_meta = load_social_font(style, style.get("social_meta_size", 18), "regular")

    width = style.get("social_width", style.get("canvas_width", 1080))
    page_height = style.get("social_min_height", 1440)
    margin_x = style.get("social_margin_x", 78)
    margin_top = style.get("social_margin_top", 76)
    margin_bottom = style.get("social_margin_bottom", 90)
    max_text_width = width - margin_x * 2
    paragraph_gap = style.get("social_paragraph_gap", 48)
    body_font_size = style.get("social_font_size", 43)
    line_height = style.get("social_line_height", body_font_size + style.get("social_line_gap", 20))
    content_start_y = margin_top + 72 + 72
    content_bottom_y = page_height - margin_bottom

    pages = paginate_blocks(
        blocks,
        font_body,
        font_heading,
        max_text_width,
        line_height,
        paragraph_gap,
        content_start_y,
        content_bottom_y,
        style,
        font_caption,
        image_dirs or [],
    )

    saved_paths = []
    page_layout = summarize_pages(pages)
    total_pages = len(pages)
    for page_index, layout in enumerate(pages, start=1):
        suffix = f"_{page_index:02d}" if total_pages > 1 else ""
        save_path = os.path.join(output_dir, f"{base_name}{suffix}.png")
        draw_social_text_page(
            layout,
            save_path,
            style,
            font_body,
            font_heading,
            font_caption,
            font_brand,
            font_brand_en,
            font_meta,
            line_height,
            title=title,
        )
        saved_paths.append(save_path)

    if return_metadata:
        return saved_paths, page_layout
    return saved_paths


def paginate_blocks(blocks, font_body, font_heading, max_text_width, line_height, paragraph_gap, content_start_y, content_bottom_y, style, font_caption, image_dirs):
    pages = []
    current_page = []
    current_y = content_start_y
    page_capacity = content_bottom_y - content_start_y

    for index, block in enumerate(blocks):
        normalized = normalize_social_block(block)
        if normalized.get("page_break_before") and current_page:
            pages.append(current_page)
            current_page = []
            current_y = content_start_y

        if normalized.get("keep_with_next") and index + 1 < len(blocks) and current_page:
            current_height = estimate_social_block_height(normalized, font_body, font_heading, max_text_width, line_height, style, font_caption, image_dirs, page_capacity)
            next_height = estimate_social_block_height(normalize_social_block(blocks[index + 1]), font_body, font_heading, max_text_width, line_height, style, font_caption, image_dirs, page_capacity)
            gap = paragraph_gap if current_page else 0
            combined_height = current_height + paragraph_gap + next_height
            if current_height <= page_capacity and combined_height <= page_capacity and current_y + gap + combined_height > content_bottom_y:
                pages.append(current_page)
                current_page = []
                current_y = content_start_y

        if normalized["kind"] == "image":
            image_block = prepare_image_block(normalized, style, max_text_width, content_bottom_y - content_start_y, font_caption, image_dirs)
            if not image_block:
                continue
            gap = paragraph_gap if current_page else 0
            if current_page and current_y + gap + image_block["height"] > content_bottom_y:
                pages.append(current_page)
                current_page = []
                current_y = content_start_y
                gap = 0
            current_page.append(image_block)
            current_y += gap + image_block["height"]
            continue

        block_font = font_heading if normalized["kind"] == "heading" else font_body
        lines = wrap_text_by_width(normalized["text"], block_font, max_text_width)
        paragraph_height = len(lines) * line_height
        gap = paragraph_gap if current_page else 0
        if (
            lines
            and paragraph_height <= page_capacity
            and current_page
            and current_y + gap + paragraph_height > content_bottom_y
        ):
            pages.append(current_page)
            current_page = []
            current_y = content_start_y

        while lines:
            gap = paragraph_gap if current_page else 0
            available_h = content_bottom_y - current_y - gap
            available_lines = int(available_h // line_height)

            if available_lines <= 0:
                if current_page:
                    pages.append(current_page)
                current_page = []
                current_y = content_start_y
                continue

            chunk = lines[:available_lines]
            lines = lines[available_lines:]
            current_page.append({
                "kind": normalized["kind"],
                "lines": chunk,
                "block_index": normalized.get("block_index"),
                "text": normalized.get("text", ""),
                "page_break_before": normalized.get("page_break_before", False),
                "keep_with_next": normalized.get("keep_with_next", False),
            })
            current_y += gap + len(chunk) * line_height

            if lines:
                pages.append(current_page)
                current_page = []
                current_y = content_start_y

    if current_page:
        pages.append(current_page)
    return pages


def estimate_social_block_height(block, font_body, font_heading, max_text_width, line_height, style, font_caption, image_dirs, page_capacity):
    if block["kind"] == "image":
        image_block = prepare_image_block(block, style, max_text_width, page_capacity, font_caption, image_dirs)
        return image_block["height"] if image_block else 0
    block_font = font_heading if block["kind"] == "heading" else font_body
    lines = wrap_text_by_width(block.get("text", ""), block_font, max_text_width)
    return len(lines) * line_height


def summarize_pages(pages):
    summary = []
    for page_index, page in enumerate(pages, start=1):
        blocks = []
        for block in page:
            block_index = block.get("block_index")
            if block_index is None:
                continue
            text = block.get("alt") if block.get("kind") == "image" else block.get("text", "")
            blocks.append({
                "block_index": block_index,
                "kind": block.get("kind"),
                "text": summarize_block_text(text),
            })
        summary.append({
            "page": page_index,
            "blocks": blocks,
        })
    return summary


def summarize_block_text(text):
    value = strip_markers(auto_format_text(str(text or ""))).strip()
    return value[:28] + "..." if len(value) > 28 else value


def normalize_social_block(block):
    if isinstance(block, dict):
        normalized = {
            "kind": block.get("kind", "body"),
            "text": block.get("text", ""),
        }
        normalized.update(block)
        return normalized
    return {"kind": "body", "text": str(block)}


def parse_image_attrs(raw_attrs):
    attrs = {}
    for token in raw_attrs.split():
        if "=" in token:
            key, value = token.split("=", 1)
            attrs[key.strip()] = value.strip().strip('"\'')
        elif token:
            attrs["layout"] = token.strip()
    return attrs


def prepare_image_block(block, style, max_text_width, page_capacity, font_caption, image_dirs):
    image_path = resolve_image_path(block.get("src", ""), image_dirs)
    if not image_path:
        return None

    try:
        with Image.open(image_path) as source:
            source_width, source_height = source.size
    except Exception:
        return None

    layout = resolve_image_layout(block, source_width, source_height)
    size = block.get("size", "auto")
    caption = auto_format_text(block.get("alt", "").strip())
    show_caption = bool(block.get("show_caption", True) and caption)
    caption_lines = wrap_text_by_width(caption, font_caption, max_text_width) if show_caption else []
    caption_height = len(caption_lines) * 30 + (14 if caption_lines else 0)
    margin_top = clamp_int(block.get("margin_top"), 0, 120, 0)
    margin_bottom = clamp_int(block.get("margin_bottom"), 0, 120, 0)
    adjustment = {
        "zoom": clamp_int(block.get("zoom"), 100, 180, 100),
        "crop_x": clamp_int(block.get("crop_x"), -100, 100, 0),
        "crop_y": clamp_int(block.get("crop_y"), -100, 100, 0),
        "margin_top": margin_top,
        "margin_bottom": margin_bottom,
    }

    if layout == "side":
        height = 330
        return {
            **block,
            **adjustment,
            "kind": "image",
            "path": image_path,
            "layout": layout,
            "height": height + margin_top + margin_bottom,
            "card_height": height,
            "caption_lines": caption_lines[:5],
            "image_box": (285, 230),
        }

    target_width = image_target_width(layout, size, max_text_width, style)
    target_height = round(target_width * source_height / source_width)
    max_image_height = image_max_height(layout, page_capacity, style)
    if target_height > max_image_height:
        target_height = max_image_height
        target_width = round(target_height * source_width / source_height)

    return {
        **block,
        **adjustment,
        "kind": "image",
        "path": image_path,
        "layout": layout,
        "height": margin_top + target_height + caption_height + margin_bottom,
        "image_height": target_height,
        "caption_lines": caption_lines,
        "image_box": (target_width, target_height),
    }


def clamp_int(value, minimum, maximum, default):
    try:
        number = int(float(value))
    except (TypeError, ValueError):
        return default
    return max(minimum, min(maximum, number))


def resolve_image_path(src, image_dirs):
    if not src or src.startswith(("http://", "https://")):
        return None
    normalized = src.replace("\\", "/").lstrip("/")
    candidates = []
    for image_dir in image_dirs:
        candidates.append(os.path.join(image_dir, normalized))
        candidates.append(os.path.join(image_dir, os.path.basename(normalized)))
    for candidate in candidates:
        candidate = os.path.abspath(candidate)
        if os.path.exists(candidate):
            return candidate
    return None


def resolve_image_layout(block, source_width, source_height):
    requested = block.get("layout", "auto")
    if requested in {"wide", "portrait", "square", "side", "full"}:
        return requested
    ratio = source_width / source_height
    alt = block.get("alt", "")
    if source_width <= 640 and len(alt) <= 36 and 0.75 <= ratio <= 1.35:
        return "side"
    if ratio >= 1.25:
        return "wide"
    if ratio <= 0.75:
        return "portrait"
    return "square"


def image_target_width(layout, size, max_text_width, style):
    size_scale = {
        "small": 0.62,
        "medium": 0.78,
        "large": 1.0,
        "auto": None,
    }.get(size, None)
    if size_scale:
        return round(max_text_width * size_scale)
    if layout == "portrait":
        return round(max_text_width * style.get("social_image_portrait_scale", 0.58))
    if layout == "square":
        return round(max_text_width * style.get("social_image_square_scale", 0.78))
    return max_text_width


def image_max_height(layout, page_capacity, style):
    if layout == "portrait":
        return round(page_capacity * style.get("social_image_portrait_max_height", 0.55))
    if layout == "square":
        return round(page_capacity * style.get("social_image_square_max_height", 0.48))
    return round(page_capacity * style.get("social_image_max_height", 0.50))


def draw_image_block(canvas, draw, block, margin_x, y, style, font_caption, text_color, muted, rule_color):
    width = style.get("social_width", style.get("canvas_width", 1080))
    max_text_width = width - margin_x * 2
    y += block.get("margin_top", 0)
    if block.get("layout") == "side":
        return draw_side_image_block(canvas, draw, block, margin_x, y, max_text_width, font_caption, text_color, muted, rule_color) + block.get("margin_bottom", 0)

    box_width, box_height = block["image_box"]
    image_x = margin_x + (max_text_width - box_width) // 2
    with Image.open(block["path"]).convert("RGB") as source:
        rendered = render_image_to_box(
            source,
            box_width,
            box_height,
            block.get("zoom", 100),
            block.get("crop_x", 0),
            block.get("crop_y", 0),
            fit="cover" if block.get("zoom", 100) > 100 else "contain",
        )
    canvas.paste(rendered, (image_x, y))
    draw.rounded_rectangle([(image_x, y), (image_x + rendered.width, y + rendered.height)], radius=3, outline=rule_color, width=1)

    current_y = y + rendered.height + 14
    for line in block.get("caption_lines", []):
        draw.text((margin_x, current_y), line, font=font_caption, fill=muted)
        current_y += 30
    return current_y + block.get("margin_bottom", 0)


def draw_side_image_block(canvas, draw, block, margin_x, y, max_text_width, font_caption, text_color, muted, rule_color):
    card_height = block.get("card_height", block["height"])
    card_x = margin_x
    card_w = max_text_width
    draw.rounded_rectangle([(card_x, y), (card_x + card_w, y + card_height)], radius=10, fill="#FBFAF5", outline=rule_color, width=1)

    image_w, image_h = block["image_box"]
    image_x = card_x + 34
    image_y = y + 42
    with Image.open(block["path"]).convert("RGB") as source:
        resized = render_image_to_box(
            source,
            image_w,
            image_h,
            block.get("zoom", 100),
            block.get("crop_x", 0),
            block.get("crop_y", 0),
            fit="cover",
        )
    paste_x = image_x + (image_w - resized.width) // 2
    paste_y = image_y + (image_h - resized.height) // 2
    canvas.paste(resized, (paste_x, paste_y))
    draw.rounded_rectangle([(paste_x, paste_y), (paste_x + resized.width, paste_y + resized.height)], radius=4, outline=rule_color, width=1)

    text_x = image_x + image_w + 42
    text_w = card_x + card_w - 34 - text_x
    title = "图片说明"
    draw.text((text_x, image_y), title, font=font_caption, fill=muted)
    text_y = image_y + 42
    caption = block.get("alt", "")
    lines = wrap_text_by_width(auto_format_text(caption), font_caption, text_w)[:5]
    for line in lines:
        draw.text((text_x, text_y), line, font=font_caption, fill=text_color)
        text_y += 32
    return y + card_height


def render_image_to_box(source, box_width, box_height, zoom=100, crop_x=0, crop_y=0, fit="contain"):
    zoom_scale = max(1.0, min(1.8, float(zoom or 100) / 100))
    if fit == "cover":
        scale = max(box_width / source.width, box_height / source.height) * zoom_scale
    else:
        scale = min(box_width / source.width, box_height / source.height) * zoom_scale

    resized_width = max(1, round(source.width * scale))
    resized_height = max(1, round(source.height * scale))
    resized = source.resize((resized_width, resized_height), Image.LANCZOS)

    if resized_width <= box_width and resized_height <= box_height:
        background = Image.new("RGB", (box_width, box_height), "#FBFAF5")
        paste_x = (box_width - resized_width) // 2
        paste_y = (box_height - resized_height) // 2
        background.paste(resized, (paste_x, paste_y))
        return background

    overflow_x = max(0, resized_width - box_width)
    overflow_y = max(0, resized_height - box_height)
    focus_x = (float(crop_x or 0) + 100) / 200
    focus_y = (float(crop_y or 0) + 100) / 200
    left = round(overflow_x * focus_x)
    top = round(overflow_y * focus_y)
    return resized.crop((left, top, left + box_width, top + box_height))


def draw_social_text_page(layout, save_path, style, font_body, font_heading, font_caption, font_brand, font_brand_en, font_meta, line_height, title=""):
    width = style.get("social_width", style.get("canvas_width", 1080))
    image_height = style.get("social_min_height", 1440)
    margin_x = style.get("social_margin_x", 78)
    margin_top = style.get("social_margin_top", 76)
    paragraph_gap = style.get("social_paragraph_gap", 48)

    img = Image.new("RGB", (width, image_height), style.get("social_bg_color", "#F4F4EF"))
    draw = ImageDraw.Draw(img)

    accent = style.get("social_accent_color", style.get("cover_accent_color", "#C8332B"))
    text_color = style.get("social_text_color", "#171717")
    muted = style.get("social_muted_color", "#686864")
    rule_color = style.get("social_rule_color", "#B9BFB7")

    draw_social_header(draw, style, font_brand, font_brand_en, font_meta, margin_x, margin_top, width, accent, text_color, muted, rule_color)

    y = margin_top + 72 + 72
    bold_state = False
    for group_index, block in enumerate(layout):
        if group_index > 0:
            y += paragraph_gap
        if block["kind"] == "image":
            y = draw_image_block(img, draw, block, margin_x, y, style, font_caption, text_color, muted, rule_color)
            continue
        is_heading = block["kind"] == "heading"
        block_font = font_heading if is_heading else font_body
        block_color = accent if is_heading else text_color
        for line in block["lines"]:
            bold_state = draw_rich_text(
                draw,
                margin_x,
                y,
                line.replace("**", "\x01"),
                font=block_font,
                base_color=block_color,
                accent_color=accent,
                init_bold=bold_state,
            )
            y += line_height

    add_film_grain(img, intensity=0.05).save(save_path, format="PNG")


def draw_social_header(draw, style, font_brand, font_brand_en, font_meta, margin_x, margin_top, width, accent, text_color, muted, rule_color):
    brand_x = margin_x + 30
    logo_line_color = style.get("social_logo_line_color", accent)
    logo_alt_color = style.get("social_logo_alt_color", accent)
    brand_name = style.get("brand_name", "Writer Studio")
    brand_bbox = draw.textbbox((brand_x, margin_top), brand_name, font=font_brand)
    anchor_top = brand_bbox[1] + 2
    anchor_bottom = brand_bbox[3] - 1
    draw.rectangle([(margin_x, anchor_top), (margin_x + 9, anchor_bottom)], fill=logo_line_color)
    draw.rectangle([(margin_x, anchor_top), (margin_x + 24, anchor_top + 5)], fill=logo_line_color)
    draw_brand_name(
        draw,
        brand_x,
        margin_top,
        brand_name,
        style.get("social_brand_accent_text", ""),
        font_brand,
        text_color,
        logo_alt_color,
    )
    brand_width = font_brand.getlength(brand_name)
    draw.text((brand_x + brand_width + 28, margin_top + 17), style.get("brand_en", "WRITER STUDIO").upper(), font=font_brand_en, fill=muted)
    date_text = datetime.now().strftime("%Y.%m.%d")
    date_bbox = font_meta.getbbox(date_text)
    draw.text((width - margin_x - (date_bbox[2] - date_bbox[0]), margin_top + 11), date_text, font=font_meta, fill=muted)

    line_y = margin_top + 66
    line_end_x = margin_x + int((width - margin_x * 2) * 0.7)
    draw.line([(margin_x, line_y), (line_end_x, line_y)], fill=rule_color, width=1)
    for tx in [margin_x, margin_x + 92, margin_x + 184, line_end_x]:
        draw.line([(tx, line_y - 5), (tx, line_y + 5)], fill=rule_color, width=1)


def draw_brand_name(draw, x, y, brand_name, accent_text, font, base_color, accent_color):
    if not accent_text or accent_text not in brand_name:
        draw.text((x, y), brand_name, font=font, fill=base_color)
        return

    current_x = x
    parts = brand_name.split(accent_text)
    for index, part in enumerate(parts):
        if part:
            draw.text((current_x, y), part, font=font, fill=base_color)
            current_x += font.getlength(part)
        if index < len(parts) - 1:
            draw.text((current_x, y), accent_text, font=font, fill=accent_color)
            current_x += font.getlength(accent_text)


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


def load_social_font(style, size, weight="regular"):
    paths = {
        "normal": "/Users/hugo/Library/Fonts/SourceHanSansSC-Normal.otf",
        "regular": "/Users/hugo/Library/Fonts/SourceHanSansSC-Regular.otf",
        "medium": "/Users/hugo/Library/Fonts/SourceHanSansSC-Medium.otf",
    }
    for key in [weight, "regular", "normal"]:
        path = paths.get(key)
        if path and os.path.exists(path):
            return ImageFont.truetype(path, size)

    theme_font = get_theme_font_path(style)
    return ImageFont.truetype(theme_font, size) if theme_font else ImageFont.load_default()


def get_theme_font_path(style):
    font_name = style.get("font_name")
    if not font_name:
        return None
    base = path_utils.get_internal_path(os.path.join("fonts", font_name))
    for ext in [".otf", ".ttf", ".ttc"]:
        if os.path.exists(base + ext):
            return base + ext
    return None


def add_film_grain(img, intensity=0.08):
    if img.mode != 'RGB':
        img = img.convert('RGB')
    noise = Image.effect_noise(img.size, (intensity - 0.02) * 255).convert('RGB')
    return Image.blend(img, noise, 0.03)
