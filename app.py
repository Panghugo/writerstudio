from writer_studio.pipeline import generate_articles
from writer_studio.renderer import set_specific_feature, set_style as set_renderer_style
from writer_studio.themes import build_style

# ================= 🚀 全局变量与接口 =================
def run_generator(target_md=None):
    """供 GUI 调用的主函数，支持指定特定文件"""
    main(target_md)

STYLE = build_style()
set_renderer_style(STYLE)

def set_style(theme_name, author_name=None):
    global STYLE
    STYLE = build_style(theme_name, author_name)
    set_renderer_style(STYLE)

def main(target_md=None, input_dir="input", output_dir="output", theme="black_gold", author_name="作者"):
    set_style(theme, author_name)
    print(f"🎨 Theme set to: {theme}")
    
    if author_name:
        print(f"✍️ Author set to: {author_name}")

    generate_articles(target_md=target_md, input_dir=input_dir, output_dir=output_dir, style=STYLE)

if __name__ == "__main__": main()
