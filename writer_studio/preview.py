from .renderers.wechat_article import render_preview_document


def export_html_preview(md_lines, output_dir, folder_name, main_title, style):
    return render_preview_document(md_lines, output_dir, folder_name, main_title, style)
