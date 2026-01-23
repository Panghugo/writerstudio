import os
import textwrap
import time
import shutil
import math
import re
import sys
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont, ImageChops, ImageFilter

import path_utils

# ================= 🚀 全局变量与接口 =================
SPECIFIC_FEATURE_NAME = None 

def set_specific_feature(filename):
    global SPECIFIC_FEATURE_NAME
    SPECIFIC_FEATURE_NAME = filename

def run_generator(target_md=None):
    """供 GUI 调用的主函数，支持指定特定文件"""
    main(target_md)

# ================= 🎨 视觉风格配置室 =================
# ================= 🎨 视觉风格配置室 =================
THEMES = {
    "black_gold": {
        "bg_color": "#FFFFFF", "font_name": "songti",
        "cover_ratio": 2.35, "cover_bg_color": "#141414", "cover_text_color": "#E6C35C", 
        "cover_main_size": 130, "cover_footer_size": 32, "cover_margin": 80,            
        "header_ratio": 0.75, "header_bg_color": "#1A1A1A", "header_text_color": "#E6C35C", 
        "header_main_size": 100, "header_sub_size": 48, "header_footer_size": 32, "header_margin": 80,           
        "footer_height": 500, "footer_bg_color": "#141414", "footer_gold": "#E6C35C",      
        "brand_name": "随时上场", "brand_en": "THE ARENA", "brand_slogan": "商业观察  /  组织重构  /  AI 进化",
        "author_text": "文 / {author}", 
        "h_bg_color": "#FFFFFF", "h_font_size": 52, "h_color": "#222222", 
        "h_padding_top": 110, "h_padding_bottom": 110,
        "h_num_radius": 38, "h_num_color": "#E6C35C", "h_num_font_size": 40, "h_text_gap": 45,
        "gif_frames": 16, "gif_duration": 100,       
        "q_bg_color": "#FFFFFF", "q_text_color": "#333333", "q_line_color": "#000000", 
        "q_font_size": 46, "q_padding_x": 120, "q_line_spacing": 35, "q_deco_gap": 100, "q_deco_width": 80,
        "q_radius": 20, "q_fold_size": 60
    },
    "tech_blue": {
        "bg_color": "#F0F4F8", "font_name": "songti",
        "cover_ratio": 2.35, "cover_bg_color": "#0F172A", "cover_text_color": "#38BDF8", 
        "cover_main_size": 130, "cover_footer_size": 32, "cover_margin": 80,            
        "header_ratio": 0.75, "header_bg_color": "#1E293B", "header_text_color": "#38BDF8", 
        "header_main_size": 100, "header_sub_size": 48, "header_footer_size": 32, "header_margin": 80,           
        "footer_height": 500, "footer_bg_color": "#0F172A", "footer_gold": "#38BDF8",      
        "brand_name": "未来科技", "brand_en": "FUTURE TECH", "brand_slogan": "深度  /  前沿  /  洞察",
        "author_text": "文 / {author}", 
        "h_bg_color": "#F8FAFC", "h_font_size": 52, "h_color": "#0F172A", 
        "h_padding_top": 110, "h_padding_bottom": 110,
        "h_num_radius": 38, "h_num_color": "#0EA5E9", "h_num_font_size": 40, "h_text_gap": 45,
        "gif_frames": 16, "gif_duration": 100,       
        "q_bg_color": "#F1F5F9", "q_text_color": "#0F172A", "q_line_color": "#38BDF8", 
        "q_font_size": 46, "q_padding_x": 120, "q_line_spacing": 35, "q_deco_gap": 100, "q_deco_width": 80,
        "q_radius": 20, "q_fold_size": 60
    },
    "paper_white": {
        "bg_color": "#FAF9F6", "font_name": "songti",
        "cover_ratio": 2.35, "cover_bg_color": "#FFFFFF", "cover_text_color": "#000000", 
        "cover_main_size": 130, "cover_footer_size": 32, "cover_margin": 80,            
        "header_ratio": 0.75, "header_bg_color": "#FFFFFF", "header_text_color": "#000000", 
        "header_main_size": 100, "header_sub_size": 48, "header_footer_size": 32, "header_margin": 80,           
        "footer_height": 500, "footer_bg_color": "#FFFFFF", "footer_gold": "#000000",      
        "brand_name": "素年锦时", "brand_en": "PURE TIME", "brand_slogan": "阅读  /  思考  /  生活",
        "author_text": "文 / {author}", 
        "h_bg_color": "#FAF9F6", "h_font_size": 52, "h_color": "#333333", 
        "h_padding_top": 110, "h_padding_bottom": 110,
        "h_num_radius": 38, "h_num_color": "#666666", "h_num_font_size": 40, "h_text_gap": 45,
        "gif_frames": 16, "gif_duration": 100,       
        "q_bg_color": "#FFFFFF", "q_text_color": "#333333", "q_line_color": "#999999", 
        "q_font_size": 46, "q_padding_x": 120, "q_line_spacing": 35, "q_deco_gap": 100, "q_deco_width": 80,
        "q_radius": 0, "q_fold_size": 0
    }
}

STYLE = THEMES["black_gold"]

def set_style(theme_name):
    global STYLE
    if theme_name in THEMES:
        STYLE = THEMES[theme_name]
    else:
        STYLE = THEMES["black_gold"]
    STYLE["canvas_width"] = 1080 # Force standard width


# ================= 🛠️ 核心功能区 =================
def get_font_path():
    # Use path_utils to find font in bundled resources
    base = path_utils.get_internal_path(os.path.join("fonts", STYLE["font_name"]))
    for ext in [".otf", ".ttf", ".ttc"]:
        if os.path.exists(base + ext): return base + ext
    print(f"⚠️ Font not found at: {base}")
    return None

def load_font(size):
    path = get_font_path()
    return ImageFont.truetype(path, size) if path else ImageFont.load_default()

def auto_format_text(text):
    text = text.replace('“', '「').replace('”', '」')
    text = re.sub(r'([\u4e00-\u9fa5])([A-Za-z0-9])', r'\1 \2', text)
    text = re.sub(r'([A-Za-z0-9])([\u4e00-\u9fa5])', r'\1 \2', text)
    return text

def process_text_lines(text, max_chars=15):
    if "|" in text: return [l.strip() for l in text.split("|") if l.strip()]
    return textwrap.wrap(text, width=max_chars)

def add_film_grain(img, intensity=0.08):
    if img.mode != 'RGB': img = img.convert('RGB')
    width, height = img.size
    noise = Image.effect_noise((width, height), (intensity-0.02) * 255).convert('RGB')
    img = Image.blend(img, noise, 0.03)
    return img

# --- 绘图函数区 ---
def draw_cover(text, save_path):
    w, h = STYLE["canvas_width"], int(STYLE["canvas_width"] / STYLE["cover_ratio"])
    img = Image.new("RGB", (w, h), STYLE["cover_bg_color"])
    draw = ImageDraw.Draw(img)
    main_title = text.split('|')[0].strip()
    margin = STYLE["cover_margin"]
    current_y = margin + 20
    draw.rectangle([(margin, current_y), (margin + 80, current_y + 6)], fill=STYLE["cover_text_color"])
    current_y += 70
    max_width = w - (margin * 2)
    current_font_size = STYLE["cover_main_size"]
    min_font_size = 60
    font_main = load_font(current_font_size)
    while font_main.getlength(main_title) > max_width and current_font_size > min_font_size:
        current_font_size -= 2
        font_main = load_font(current_font_size)
    draw.text((margin, current_y), main_title, font=font_main, fill=STYLE["cover_text_color"])
    font_footer = load_font(STYLE["cover_footer_size"])
    date_str = datetime.now().strftime("%b %d, %Y").upper()
    footer_text = f"{STYLE['author_text']}   ·   {date_str}"
    bbox = font_footer.getbbox(footer_text)
    f_x, f_y = w - margin - (bbox[2]-bbox[0]), h - margin - (bbox[3]-bbox[1])
    draw.line([(0, f_y - 40), (w, f_y - 40)], fill=STYLE["cover_text_color"], width=1)
    draw.text((f_x, f_y), footer_text, font=font_footer, fill=STYLE["cover_text_color"])
    add_film_grain(img).save(save_path)

def draw_header(text, save_path, read_time_mins, asset_dir="input"):
    global SPECIFIC_FEATURE_NAME
    # Reset SPECIFIC_FEATURE_NAME to ensure we check for latest feature image
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
    while font_main.getlength(main_title) > max_width and main_font_size > 40:
        main_font_size -= 2
        font_main = load_font(main_font_size)
    draw.text((margin, current_y), main_title, font=font_main, fill=STYLE["header_text_color"])
    bbox_main = font_main.getbbox(main_title)
    current_y += (bbox_main[3] - bbox_main[1]) + 40
    
    if sub_title:
        current_y += 10
        draw.rectangle([(margin, current_y), (margin + 60, current_y+4)], fill=STYLE["header_text_color"])
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
    if SPECIFIC_FEATURE_NAME:
        p = os.path.join(asset_dir, SPECIFIC_FEATURE_NAME)
        if os.path.exists(p): feature_path = p
    
    if not feature_path:
        for candidate in ["feature.png", "feature.jpg", "feature.jpeg"]:
            p = os.path.join(asset_dir, candidate)
            if os.path.exists(p): feature_path = p; break

    if feature_path:
        try:
            f_img = Image.open(feature_path).convert("RGBA")
            if available_h > 100:
                ratio = f_img.width / f_img.height
                new_h = int(target_w / ratio)
                if new_h > available_h: new_h = available_h; target_w = int(new_h * ratio); final_x = (w - target_w) // 2
                else: final_x = margin
                f_img = f_img.resize((target_w, new_h), Image.LANCZOS)
                img.paste(f_img, (final_x, text_end_y), f_img)
        except: pass
    elif available_h > 200:
        cx, cy, r = w // 2, text_end_y + (available_h // 2), 80
        draw.ellipse([(cx-r, cy-r), (cx+r, cy+r)], outline=STYLE["header_text_color"], width=1)
        draw.ellipse([(cx-r*1.5, cy-r*1.5), (cx+r*1.5, cy+r*1.5)], outline=STYLE["header_text_color"], width=1)
        draw.line([(cx, cy-r*2), (cx, cy+r*2)], fill=STYLE["header_text_color"], width=1)
        
    draw.text((margin, y_line1), STYLE['author_text'], font=font_footer, fill=STYLE["header_text_color"])
    draw.text((margin, y_line2), datetime.now().strftime("%B %d, %Y").upper(), font=font_footer, fill=STYLE["header_text_color"])
    read_text = f"预计阅读 {read_time_mins} 分钟"
    bbox_r = font_footer.getbbox(read_text)
    draw.text((w - margin - (bbox_r[2]-bbox_r[0]), y_line2), read_text, font=font_footer, fill=STYLE["header_text_color"])
    add_film_grain(img).save(save_path)

def draw_footer_card(save_path, asset_dir="input"):
    w, h = STYLE["canvas_width"], 500
    img = Image.new("RGB", (w, h), STYLE["footer_bg_color"])
    draw = ImageDraw.Draw(img)
    margin = 80
    draw.line([(0, 0), (w, 0)], fill=STYLE["footer_gold"], width=6)
    content_h = 240
    start_y = (h - content_h) // 2
    draw.text((margin, start_y), STYLE["brand_name"], font=load_font(90), fill=STYLE["footer_gold"])
    draw.text((margin, start_y + 110), STYLE["brand_en"], font=load_font(32), fill="#666666", spacing=10)
    draw.text((margin, start_y + 180), STYLE["brand_slogan"], font=load_font(28), fill="#888888")
    qr_path = os.path.join(asset_dir, "qrcode.png")
    if os.path.exists(qr_path):
        try:
            qr_size = 200
            qr_img = Image.open(qr_path).convert("RGBA").resize((qr_size, qr_size))
            base_size = qr_size + 20
            draw.rectangle([(w - margin - base_size, (h-base_size)//2), (w - margin, (h-base_size)//2 + base_size)], fill=STYLE["footer_gold"])
            qr_bg = Image.new("RGBA", (qr_size+8, qr_size+8), "WHITE")
            qr_bg.paste(qr_img, (4, 4), qr_img)
            img.paste(qr_bg, (w - margin - base_size + 10 - 4, (h - base_size) // 2 + 10 - 4))
        except: pass
    add_film_grain(img).save(save_path)

def draw_heading_gif(text, save_path, index):
    font, num_font = load_font(STYLE["h_font_size"]), load_font(STYLE["h_num_font_size"])
    w, cx = STYLE["canvas_width"], STYLE["canvas_width"] // 2
    lines = process_text_lines(text)
    total_text_h = sum([font.getbbox(l)[3]-font.getbbox(l)[1] for l in lines]) + (len(lines)*25) - 25
    img_h = STYLE["h_padding_top"] + (STYLE["h_num_radius"] * 2) + STYLE["h_text_gap"] + total_text_h + STYLE["h_padding_bottom"]
    frames = [] 
    for f in range(STYLE["gif_frames"]):
        img = Image.new("RGB", (w, img_h), STYLE["h_bg_color"])
        d = ImageDraw.Draw(img)
        offset = math.sin((f/STYLE["gif_frames"])*math.pi) * 4  
        cy, br = STYLE["h_padding_top"] + STYLE["h_num_radius"], STYLE["h_num_radius"]
        d.line([(0, 20), (w, 20)], fill=STYLE["h_num_color"], width=4)
        d.line([(0, 32), (w, 32)], fill=STYLE["h_num_color"], width=1)
        d.ellipse([(cx-(br+offset), cy-(br+offset)), (cx+(br+offset), cy+(br+offset))], outline=STYLE["h_num_color"], width=1)
        d.ellipse([(cx-(br-6+offset*0.6), cy-(br-6+offset*0.6)), (cx+(br-6+offset*0.6), cy+(br-6+offset*0.6))], outline=STYLE["h_num_color"], width=2)
        n_txt = str(index)
        nb = num_font.getbbox(n_txt)
        d.text((cx-(nb[2]-nb[0])//2, cy-(nb[3]-nb[1])//2-nb[1]-2), n_txt, font=num_font, fill=STYLE["h_num_color"])
        cy_t = cy + br + STYLE["h_text_gap"]
        for l in lines:
            lb = font.getbbox(l)
            d.text((cx-(lb[2]-lb[0])//2, cy_t), l, font=font, fill=STYLE["h_color"])
            cy_t += (lb[3]-lb[1]) + 25
        d.line([(0, img_h-20), (w, img_h-20)], fill=STYLE["h_num_color"], width=4)
        frames.append(img)
    frames[0].save(save_path, save_all=True, append_images=frames[1:], duration=STYLE["gif_duration"], loop=0)

def draw_quote(text, save_path):
    font = load_font(STYLE["q_font_size"])
    w = STYLE["canvas_width"]
    qm_font = ImageFont.truetype(get_font_path(), STYLE["q_font_size"]*4) if get_font_path() else font
    lines = process_text_lines(text, (w-STYLE["q_padding_x"]*2)//STYLE["q_font_size"])
    total_h = sum([font.getbbox(l)[3]-font.getbbox(l)[1] for l in lines]) + (len(lines)*STYLE["q_line_spacing"]) - STYLE["q_line_spacing"]
    img_h = total_h + (STYLE["q_deco_gap"] * 2)
    mask = Image.new("L", (w, img_h), 0)
    draw_mask = ImageDraw.Draw(mask)
    r = STYLE["q_radius"]
    draw_mask.rounded_rectangle([(0,0), (w, img_h)], radius=r, fill=255)
    fold_size = STYLE["q_fold_size"]
    cut_poly = [(w, img_h), (w, img_h - fold_size), (w - fold_size, img_h)]
    draw_mask.polygon(cut_poly, fill=0) 
    card_color_layer = Image.new("RGBA", (w, img_h), STYLE["q_bg_color"])
    img = Image.new("RGBA", (w, img_h), (0,0,0,0)) 
    img.paste(card_color_layer, mask=mask)
    d = ImageDraw.Draw(img)
    # Watermark Quote Mark (Grey, Transparent, Behind Text)
    watermark_color = (200, 200, 200, 60) # RGBA: Light Grey, Low Opacity
    d.text((STYLE["q_padding_x"]-40, STYLE["q_deco_gap"]-40), "“", font=qm_font, fill=watermark_color)
    for y in [STYLE["q_deco_gap"]-50, img_h-STYLE["q_deco_gap"]+50]:
        d.line([(w//2-STYLE["q_deco_width"], y), (w//2+STYLE["q_deco_width"], y)], fill=STYLE["q_line_color"], width=4)
        d.regular_polygon((w//2, y, 6), 4, rotation=0, fill=STYLE["q_line_color"])
    cy = (img_h - total_h) // 2
    for l in lines:
        lx = w - (font.getbbox(l)[2]-font.getbbox(l)[0]) - (STYLE["q_padding_x"]+20) if l.startswith(("——","--")) else (w - (font.getbbox(l)[2]-font.getbbox(l)[0])) // 2
        d.text((lx, cy), l, font=font, fill=STYLE["q_text_color"])
        cy += (font.getbbox(l)[3]-font.getbbox(l)[1]) + STYLE["q_line_spacing"]
    flap_poly = [(w - fold_size, img_h - fold_size), (w, img_h - fold_size), (w - fold_size, img_h)]
    d.polygon(flap_poly, fill="#F2F2F2", outline=None)
    d.line([(w - fold_size, img_h), (w - fold_size, img_h - fold_size), (w, img_h - fold_size)], fill=STYLE["footer_gold"], width=1)
    d.line([(w - fold_size, img_h), (w, img_h - fold_size)], fill="#E0E0E0", width=1)
    img.save(save_path, format="PNG")

def export_html_preview(md_lines, output_dir, folder_name, main_title):
    print(f"   ⚡ 正在生成双模预览: {main_title}...")
    try:
        html_content = []
        # 添加样式，让预览更接近最终效果
        html_content.append(f"""<!DOCTYPE html>
<html>
<head>
    <meta charset='utf-8'>
    <title>{main_title}</title>
    <style>
        body {{ font-family: 'PingFang SC', 'Microsoft YaHei', sans-serif; background: #f5f5f5; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; background: white; }}
        p {{ line-height: 1.8; color: #333; margin-bottom: 20px; }}
        .bold-text {{ color: #E6C35C; font-weight: bold; }}
        img {{ width: 100%; margin: 20px 0; display: block; }}
    </style>
</head>
<body>
<div class='container'>
""")
        
        # Generate timestamp for cache busting
        cache_buster = int(time.time() * 1000)
        
        for line in md_lines:
            line = line.strip()
            if not line: continue
            
            if line.startswith("![]"):
                # 修复图片路径并添加缓存破坏参数
                match = re.search(r'\((.*?)\)', line)
                if match: 
                    img_path = match.group(1)
                    # Add cache-busting parameter to prevent browser caching
                    img_url = f"{img_path}?t={cache_buster}"
                    html_content.append(f'<img src="{img_url}" alt="图片" />')
            else:
                # 处理加粗文字 **文字** -> 金色样式
                processed_line = re.sub(r'\*\*(.+?)\*\*', r'<span class="bold-text">\1</span>', line)
                html_content.append(f'<p>{processed_line}</p>')
        
        html_content.append("</div></body></html>")
        html_path = os.path.join(output_dir, f"PREVIEW_{folder_name}.html")
        with open(html_path, "w", encoding="utf-8") as f: 
            f.write("\n".join(html_content))
    except Exception as e: 
        print(f"❌ HTML 生成失败: {e}")

def main(target_md=None, input_dir="input", output_dir="output", theme="black_gold", author_name="作者"):
    # Set Theme
    set_style(theme)
    print(f"🎨 Theme set to: {theme}")
    
    # Replace author placeholder with actual author name
    if author_name and '{author}' in STYLE.get('author_text', ''):
        STYLE['author_text'] = STYLE['author_text'].replace('{author}', author_name)
        print(f"✍️ Author set to: {author_name}")

    if not os.path.exists(input_dir): os.makedirs(input_dir)
    if not os.path.exists(output_dir): os.makedirs(output_dir)
    
    # === 关键修改 ===
    # 如果指定了文件，只处理这一个；否则处理全部
    if target_md:
        files = [target_md]
    else:
        files = [f for f in os.listdir(input_dir) if f.endswith(".md")]
        
    if not files: return print(f"❌ {input_dir} 文件夹里没有 Markdown 文件！")

    for md_file in files:
        # 增加一道保险：如果文件不存在（比如文件名乱码对不上），跳过
        if not os.path.exists(os.path.join(input_dir, md_file)):
            print(f"⚠️ 跳过不存在的文件: {md_file}")
            continue
            
        print(f"📄 处理中: {md_file}")
        with open(os.path.join(input_dir, md_file), "r", encoding="utf-8") as f: full_text = f.read()
        mins = max(1, math.ceil(len(full_text) / 400))
        fname = os.path.splitext(md_file)[0]
        out_dir = os.path.join(output_dir, fname)
        assets = os.path.join(out_dir, "assets")
        if os.path.exists(out_dir): shutil.rmtree(out_dir)
        os.makedirs(assets)
        
        lines, new_con, h_cnt = full_text.splitlines(), [], 0
        main_title = "未命名文章"
        
        for i, line in enumerate(lines):
            line = auto_format_text(line.strip())
            ts = int(time.time() * 10000) + i
            
            if line.startswith("# "):
                txt = line.replace("# ", "").strip()
                main_title = txt.split('|')[0]
                if txt:
                    draw_cover(txt, os.path.join(assets, f"COVER_{ts}.png"))
                    hn = f"HEADER_{ts}.png"
                    draw_header(txt, os.path.join(assets, hn), mins, asset_dir=input_dir)
                    new_con.append(f"![](assets/{hn})\n\n")
            elif line.startswith("## "):
                txt = line.replace("## ", "").strip()
                if txt:
                    h_cnt += 1
                    draw_heading_gif(txt, os.path.join(assets, f"H_{ts}.gif"), h_cnt)
                    new_con.append(f"\n![](assets/H_{ts}.gif)\n")
            elif line.startswith("> "):
                txt = line.replace("> ", "").strip()
                if txt:
                    draw_quote(txt, os.path.join(assets, f"Q_{ts}.png"))
                    new_con.append(f"\n![](assets/Q_{ts}.png)\n")
            elif line.startswith("!["):
                match = re.search(r'\((.*?)\)', line)
                if match:
                    src_path = match.group(1)
                    possible_paths = [src_path, os.path.join(input_dir, src_path), os.path.join(input_dir, os.path.basename(src_path))]
                    found = False
                    for p in possible_paths:
                        if os.path.exists(p) and os.path.isfile(p):
                            ext = os.path.splitext(p)[1]
                            new_name = f"IMG_{ts}{ext}"
                            shutil.copy(p, os.path.join(assets, new_name))
                            new_con.append(f"![](assets/{new_name})\n")
                            found = True
                            break
                    if not found: new_con.append(line + "\n")
            else:
                new_con.append(line + "\n" if line else "\n")
        
        # Footer has been removed as per user request
        # footer_name = "FOOTER.png"
        # draw_footer_card(os.path.join(assets, footer_name), asset_dir=input_dir)
        # new_con.append(f"\n\n![](assets/{footer_name})\n")

        with open(os.path.join(out_dir, "FINAL_" + md_file), "w", encoding="utf-8") as f: f.writelines(new_con)
        export_html_preview(new_con, out_dir, fname, main_title)

if __name__ == "__main__": main()