import customtkinter as ctk
import sys
import threading
import os
import json
import shutil 
import zipfile 
import time
import tkinter.messagebox
from tkinter import filedialog
from tkinter import Text, END, INSERT
from PIL import Image, ImageGrab, ImageTk
import io
import base64
import re
import html

import path_utils
import os

# Initialize config from template if needed (for packaged app)
path_utils.init_config_if_needed()

# CRITICAL: Set CWD before importing other modules (app, publisher) 
# because they might execute code at module level that relies on relative paths (e.g. publisher loading config).
os.chdir(path_utils.get_user_path())

import app
import publisher

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class RichTextEditor(tkinter.Toplevel):
    """富文本编辑器窗口 - 纯tkinter实现"""
    def __init__(self, parent, initial_filename=None):
        super().__init__(parent)
        self.parent = parent
        self.initial_filename = initial_filename
        self.title(f"快速编辑器 - {'正在编辑: ' + initial_filename if initial_filename else '粘贴飞书/Notion内容'}")
        self.geometry("900x700")
        self.configure(bg="#1e1e1e")
        self.images = []
        self.image_counter = 0
        self.draft_file = "input/.draft_autosave.md"  # 草稿文件路径
        self.autosave_id = None  # 定时器ID
        
        # 顶部工具栏 - 黑金主题
        toolbar = tkinter.Frame(self, bg="#2b2b2b", height=60)
        toolbar.pack(fill="x", padx=0, pady=0)
        toolbar.pack_propagate(False)
        
        help_label = tkinter.Label(
            toolbar,
            text="提示: 在下方直接输入或粘贴文字，点击按钮插入图片",
            bg="#2b2b2b",
            fg="#E6C35C",
            font=("PingFang SC", 13, "bold")
        )
        help_label.pack(side="left", padx=20, pady=15)
        
        # 美化的添加图片按钮 - 金色文字
        add_img_btn = tkinter.Button(
            toolbar,
            text="+ 添加图片",
            bg="#3a3a3a",  # 深灰背景
            fg="#E6C35C",  # 金色文字
            font=("PingFang SC", 12, "bold"),
            relief="flat",
            padx=20,
            pady=8,
            cursor="hand2",
            command=self.add_image,
            activebackground="#4a4a4a",  # 鼠标悬停变亮
            activeforeground="#E6C35C"
        )
        add_img_btn.pack(side="right", padx=20, pady=15)
        
        # 格式工具栏 - Markdown快捷按钮
        format_toolbar = tkinter.Frame(self, bg="#333333", height=50)
        format_toolbar.pack(fill="x", padx=0, pady=0)
        format_toolbar.pack_propagate(False)
        
        # 工具栏标签
        tkinter.Label(
            format_toolbar,
            text="格式工具:",
            bg="#333333",
            fg="#aaaaaa",
            font=("PingFang SC", 11)
        ).pack(side="left", padx=20)
        
        # H1按钮
        tkinter.Button(
            format_toolbar,
            text="# H1",
            bg="#3a3a3a",
            fg="#E6C35C",
            font=("PingFang SC", 11, "bold"),
            relief="flat",
            padx=15,
            pady=5,
            cursor="hand2",
            command=lambda: self.format_text("h1"),
            activebackground="#4a4a4a",
            activeforeground="#E6C35C"
        ).pack(side="left", padx=5)
        
        # H2按钮
        tkinter.Button(
            format_toolbar,
            text="## H2",
            bg="#3a3a3a",
            fg="#E6C35C",
            font=("PingFang SC", 11, "bold"),
            relief="flat",
            padx=15,
            pady=5,
            cursor="hand2",
            command=lambda: self.format_text("h2"),
            activebackground="#4a4a4a",
            activeforeground="#E6C35C"
        ).pack(side="left", padx=5)
        
        # 加粗按钮
        tkinter.Button(
            format_toolbar,
            text="** 加粗",
            bg="#3a3a3a",
            fg="#E6C35C",
            font=("PingFang SC", 11, "bold"),
            relief="flat",
            padx=15,
            pady=5,
            cursor="hand2",
            command=lambda: self.format_text("bold"),
            activebackground="#4a4a4a",
            activeforeground="#E6C35C"
        ).pack(side="left", padx=5)
        
        # 引用按钮
        tkinter.Button(
            format_toolbar,
            text="> 引用",
            bg="#3a3a3a",
            fg="#E6C35C",
            font=("PingFang SC", 11, "bold"),
            relief="flat",
            padx=15,
            pady=5,
            cursor="hand2",
            command=lambda: self.format_text("quote"),
            activebackground="#4a4a4a",
            activeforeground="#E6C35C"
        ).pack(side="left", padx=5)
        
        # 提示文字
        tkinter.Label(
            format_toolbar,
            text="← 选中文字后点击按钮添加格式",
            bg="#333333",
            fg="#666666",
            font=("PingFang SC", 10)
        ).pack(side="left", padx=15)
        
        # 编辑器区域
        editor_container = tkinter.Frame(self, bg="#1e1e1e")
        editor_container.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Text编辑器 - 完全可编辑
        self.text_widget = Text(
            editor_container,
            wrap="word",
            font=("PingFang SC", 14),
            bg="#2b2b2b",
            fg="#ffffff",
            insertbackground="#E6C35C",
            selectbackground="#4a4a4a",
            spacing1=5,
            spacing3=5,
            padx=15,
            pady=15,
            undo=True,
            state="normal",
            relief="flat",
            borderwidth=0
        )
        self.text_widget.pack(fill="both", expand=True)
        
        # 添加提示文字
        hint_text = """在这里输入或粘贴你的内容...

使用说明：
• 直接打字或粘贴文字（Cmd+V）
• 点击上方「+ 添加图片」按钮插入图片
• 格式：使用 # 标记标题，** 标记加粗，> 标记引用

提示：
- # 文章标题 （一级标题，生成封面）
- ## 章节标题 （二级标题，生成动画）
- **关键词** （显示为金色）
- > 金句引用 （生成卡片）

选中这段文字，按Delete删除即可开始编辑！
"""
        self.text_widget.insert("1.0", hint_text)
        self.text_widget.focus_set()
        
        # 底部操作区 - 黑金主题
        bottom_frame = tkinter.Frame(self, bg="#2b2b2b", height=70)
        bottom_frame.pack(fill="x", padx=0, pady=0)
        bottom_frame.pack_propagate(False)
        
        # 文件名标签
        tkinter.Label(
            bottom_frame,
            text="文件名:",
            bg="#2b2b2b",
            fg="white",
            font=("PingFang SC", 13)
        ).pack(side="left", padx=(20, 10), pady=20)
        
        # 文件名输入框
        self.filename_entry = tkinter.Entry(
            bottom_frame,
            width=25,
            bg="#333333",
            fg="white",
            insertbackground="#E6C35C",
            font=("PingFang SC", 13),
            relief="flat",
            borderwidth=2
        )
        self.filename_entry.pack(side="left", padx=(0, 20), pady=20, ipady=8)
        
        # 预填文件名
        if self.initial_filename:
            self.filename_entry.insert(0, self.initial_filename)
        
        # 保存并生成按钮 - 金色主题
        save_btn = tkinter.Button(
            bottom_frame,
            text="保存并生成排版",
            bg="#E6C35C",
            fg="black",
            font=("PingFang SC", 13, "bold"),
            relief="flat",
            padx=25,
            pady=10,
            cursor="hand2",
            command=self.save_and_generate,
            activebackground="#D4B04C",
            activeforeground="black"
        )
        save_btn.pack(side="left", padx=5, pady=20)
        
        # 清空按钮 - 深灰主题
        clear_btn = tkinter.Button(
            bottom_frame,
            text="清空",
            bg="#3a3a3a",
            fg="#aaaaaa",
            font=("PingFang SC", 12),
            relief="flat",
            padx=20,
            pady=10,
            cursor="hand2",
            command=self.clear_editor,
            activebackground="#4a4a4a",
            activeforeground="#cccccc"
        )
        clear_btn.pack(side="left", padx=5, pady=20)
        
        # 检查并恢复草稿
        self.check_and_restore_draft()
        
        # 启动自动保存（每30秒）
        self.start_autosave()
        
        # 绑定关闭窗口事件
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def format_text(self, format_type):
        """格式化选中的文字"""
        try:
            # 获取选中的文字
            try:
                sel_start = self.text_widget.index("sel.first")
                sel_end = self.text_widget.index("sel.last")
                selected_text = self.text_widget.get(sel_start, sel_end)
            except:
                # 没有选中文字
                tkinter.messagebox.showinfo("提示", "请先选中要格式化的文字")
                return
            
            if not selected_text.strip():
                return
            
            # 根据格式类型处理
            if format_type == "h1":
                # 一级标题 - 在行首添加 #
                lines = selected_text.split('\n')
                formatted = '\n'.join([f"# {line.lstrip('#').strip()}" if line.strip() else line for line in lines])
                
            elif format_type == "h2":
                # 二级标题 - 在行首添加 ##
                lines = selected_text.split('\n')
                formatted = '\n'.join([f"## {line.lstrip('#').strip()}" if line.strip() else line for line in lines])
                
            elif format_type == "bold":
                # 加粗 - 添加 **
                formatted = f"**{selected_text}**"
                
            elif format_type == "quote":
                # 引用 - 在行首添加 >
                lines = selected_text.split('\n')
                formatted = '\n'.join([f"> {line.lstrip('>').strip()}" if line.strip() else line for line in lines])
            else:
                return
            
            # 替换选中的文字
            self.text_widget.delete(sel_start, sel_end)
            self.text_widget.insert(sel_start, formatted)
            
            # 重新选中格式化后的文字
            new_end = f"{sel_start}+{len(formatted)}c"
            self.text_widget.tag_add("sel", sel_start, new_end)
            
            print(f"[编辑器] 已应用格式: {format_type}")
            
        except Exception as e:
            print(f"[编辑器] 格式化失败: {e}")
    
    def add_image(self):
        """添加图片（通过文件选择）"""
        file_path = filedialog.askopenfilename(
            title="选择图片",
            filetypes=[("图片文件", "*.png *.jpg *.jpeg *.gif")]
        )
        
        if not file_path:
            return
        
        try:
            # 清除占位符
            self.clear_placeholder()
            
            # 读取图片
            pil_image = Image.open(file_path)
            
            # 保存图片
            self.image_counter += 1
            img_filename = f"pasted_image_{self.image_counter}.png"
            img_path = os.path.join("input", img_filename)
            
            # 确保input目录存在
            os.makedirs("input", exist_ok=True)
            
            # 保存原图
            pil_image.save(img_path)
            
            # 创建缩略图用于显示
            display_img = pil_image.copy()
            display_img.thumbnail((500, 300), Image.LANCZOS)
            photo = ImageTk.PhotoImage(display_img)
            
            # 保存引用（防止被垃圾回收）
            self.images.append(photo)
            
            # 插入到文本中
            self.text_widget.insert(INSERT, "\n")
            self.text_widget.image_create(INSERT, image=photo)
            self.text_widget.insert(INSERT, f"\n![图片]({img_filename})\n\n")
            
            print(f"[编辑器] 图片已添加: {img_filename}")
            
        except Exception as e:
            print(f"[编辑器] 图片添加失败: {e}")
            tkinter.messagebox.showerror("错误", f"图片添加失败：{str(e)}")
    
    def extract_markdown(self):
        """从编辑器内容提取Markdown"""
        content = self.text_widget.get("1.0", END).strip()
        
        # 基础清理
        lines = content.split('\n')
        markdown_lines = []
        
        for line in lines:
            line = line.strip()
            
            # 保留空行，但不保留多余空格
            if not line:
                markdown_lines.append('')
                continue
            
            # 保留所有内容
            markdown_lines.append(line)
        
        return '\n'.join(markdown_lines)
    
    def clean_notion_spacing(self, content):
        """处理Notion导出的多余空行"""
        # 1. 连续三个及以上的换行符替换为两个
        content = re.sub(r'\n{3,}', '\n\n', content)
        # 2. 段落结尾如果是多余空格，去掉
        content = re.sub(r' +$', '', content, flags=re.M)
        return content

    def parse_and_insert_content(self, content):
        """解析Markdown内容并插入到编辑器，包括图片显示"""
        self.text_widget.delete("1.0", END)
        self.images.clear()
        
        # 清理Notion多余空行
        content = self.clean_notion_spacing(content)
        
        lines = content.split('\n')
        for i, line in enumerate(lines):
            # 匹配 Markdown 图片语法: ![alt](path)
            img_match = re.search(r'!\[.*?\]\((.*?)\)', line)
            if img_match:
                img_path = img_match.group(1)
                # 尝试在 input 目录下寻找图片
                possible_paths = [
                    os.path.join("input", img_path),
                    os.path.join("input", os.path.basename(img_path))
                ]
                
                found_img = False
                for p in possible_paths:
                    if os.path.exists(p):
                        try:
                            pil_img = Image.open(p)
                            display_img = pil_img.copy()
                            display_img.thumbnail((600, 400), Image.LANCZOS)
                            photo = ImageTk.PhotoImage(display_img)
                            self.images.append(photo)
                            
                            # 插入图片
                            self.text_widget.image_create(END, image=photo)
                            self.text_widget.insert(END, f"\n{line}\n")
                            found_img = True
                            break
                        except Exception as e:
                            print(f"[编辑器] 加载图片预览失败: {e}")
                
                if found_img:
                    continue
            
            self.text_widget.insert(END, line + ("\n" if i < len(lines)-1 else ""))
        
        # 滚动到顶部
        self.text_widget.see("1.0")

    def reload_with_file(self, filename):
        """重新加载指定文件到编辑器"""
        self.initial_filename = filename
        self.title(f"快速编辑器 - 正在编辑: {filename}")
        self.filename_entry.delete(0, END)
        self.filename_entry.insert(0, filename)
        
        target_md = os.path.join("input", f"{filename}.md")
        if os.path.exists(target_md):
            try:
                with open(target_md, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.parse_and_insert_content(content)
                print(f"[编辑器] 已重新加载文件: {target_md}")
            except Exception as e:
                print(f"[编辑器] 重新加载文件失败: {e}")

    def save_to_disk_silent(self):
        """静默保存当前内容到磁盘"""
        filename = self.filename_entry.get().strip()
        if not filename:
            return False
            
        try:
            markdown_content = self.extract_markdown()
            if not markdown_content:
                return False
                
            md_path = os.path.join("input", f"{filename}.md")
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            
            # 更新主窗口文件名
            self.parent.file_entry.delete(0, "end")
            self.parent.file_entry.insert(0, filename)
            
            self.clear_draft()
            print(f"[编辑器] 已自动保存内容到: {md_path}")
            return True
        except Exception as e:
            print(f"[编辑器] 自动保存失败: {e}")
            return False

    def save_and_generate(self):
        """保存为Markdown并触发生成排版"""
        if self.save_to_disk_silent():
            filename = self.filename_entry.get().strip()
            # 关闭编辑器窗口
            self.destroy()
            
            # 提示并询问是否生成
            result = tkinter.messagebox.askyesno(
                "保存成功",
                f"内容已保存！\n\n文件名: {filename}\n\n是否立即生成排版？"
            )
            
            if result:
                self.parent.run_generation_thread()
    
    def clear_editor(self):
        """清空编辑器"""
        self.text_widget.delete("1.0", END)
        self.images.clear()
        self.image_counter = 0
        self.filename_entry.delete(0, "end")
        print("[编辑器] 已清空")
    
    def check_and_restore_draft(self):
        """检查并恢复未保存的草稿"""
        if os.path.exists(self.draft_file):
            try:
                with open(self.draft_file, 'r', encoding='utf-8') as f:
                    draft_content = f.read()
                
                if draft_content.strip():
                    # 询问是否恢复草稿
                    result = tkinter.messagebox.askyesno(
                        "发现未保存的草稿",
                        "检测到上次编辑的内容未保存，是否恢复？\n\n点击「是」恢复草稿\n点击「否」开始新编辑",
                        icon='question'
                    )
                    
                    if result:
                        # 恢复草稿
                        self.parse_and_insert_content(draft_content)
                        print("[自动保存] 已恢复草稿")
                        return
                    else:
                        # 不恢复，删除草稿
                        os.remove(self.draft_file)
                        print("[自动保存] 已丢弃旧草稿")
            except Exception as e:
                print(f"[自动保存] 恢复草稿失败: {e}")
                
        # 加载文件内容
        current_content = self.text_widget.get("1.0", END).strip()
        is_default_hint = current_content.startswith("在这里输入或粘贴你的内容")
        
        if is_default_hint and self.initial_filename:
            try:
                target_md = os.path.join("input", f"{self.initial_filename}.md")
                if os.path.exists(target_md):
                    with open(target_md, 'r', encoding='utf-8') as f:
                        file_content = f.read()
                    
                    if file_content:
                        self.parse_and_insert_content(file_content)
                        print(f"[编辑器] 已加载已有文件: {target_md}")
            except Exception as e:
                print(f"[编辑器] 加载文件失败: {e}")
    
    def start_autosave(self):
        """启动自动保存定时器"""
        self.autosave_draft()
        # 每30秒保存一次
        self.autosave_id = self.after(30000, self.start_autosave)
    
    def autosave_draft(self):
        """自动保存草稿"""
        try:
            content = self.text_widget.get("1.0", END).strip()
            
            # 只有内容不为空且不是默认提示文字时才保存
            if content and not content.startswith("在这里输入或粘贴你的内容"):
                os.makedirs("input", exist_ok=True)
                with open(self.draft_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                print("[自动保存] 草稿已保存")
        except Exception as e:
            print(f"[自动保存] 保存失败: {e}")
    
    def clear_draft(self):
        """清除草稿文件"""
        try:
            if os.path.exists(self.draft_file):
                os.remove(self.draft_file)
                print("[自动保存] 草稿已清除")
        except Exception as e:
            print(f"[自动保存] 清除草稿失败: {e}")
    
    def on_closing(self):
        """关闭窗口时的处理"""
        # 取消定时器
        if self.autosave_id:
            self.after_cancel(self.autosave_id)
        
        # 保存最后一次草稿
        self.autosave_draft()
        
        # 关闭窗口
        self.destroy()
        print("[编辑器] 窗口已关闭")

class SetupWizard(ctk.CTkToplevel):
    """首次运行配置向导"""
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("欢迎使用 Writer Studio")
        self.geometry("500x550")
        self.resizable(False, False)
        self.attributes("-topmost", True)
        
        # 使窗口模态化
        self.grab_set()
        
        # 欢迎标题
        self.welcome_label = ctk.CTkLabel(
            self, 
            text="🎉 欢迎使用 Writer Studio", 
            font=ctk.CTkFont(size=20, weight="bold")
        )
        self.welcome_label.pack(pady=(30, 10))
        
        # 说明文字
        self.info_label = ctk.CTkLabel(
            self,
            text="首次使用需要配置微信公众号信息\n用于发布文章到微信公众平台",
            font=ctk.CTkFont(size=13),
            text_color="#888888"
        )
        self.info_label.pack(pady=(0, 20))
        
        # 配置表单
        self.frame = ctk.CTkFrame(self, fg_color="#2b2b2b")
        self.frame.pack(padx=30, fill="both", expand=True)
        
        # AppID
        ctk.CTkLabel(
            self.frame, 
            text="微信公众号 AppID:", 
            anchor="w",
            font=ctk.CTkFont(size=13, weight="bold")
        ).pack(fill="x", pady=(20, 5), padx=20)
        
        self.entry_appid = ctk.CTkEntry(
            self.frame, 
            placeholder_text="例如: wx1234567890abcdef",
            height=35
        )
        self.entry_appid.pack(fill="x", pady=(0, 15), padx=20)
        
        # AppSecret
        ctk.CTkLabel(
            self.frame, 
            text="AppSecret (密钥):", 
            anchor="w",
            font=ctk.CTkFont(size=13, weight="bold")
        ).pack(fill="x", pady=(5, 5), padx=20)
        
        self.entry_secret = ctk.CTkEntry(
            self.frame, 
            show="●",
            placeholder_text="输入您的AppSecret",
            height=35
        )
        self.entry_secret.pack(fill="x", pady=(0, 15), padx=20)
        
        # 作者名
        ctk.CTkLabel(
            self.frame, 
            text="默认作者名:", 
            anchor="w",
            font=ctk.CTkFont(size=13, weight="bold")
        ).pack(fill="x", pady=(5, 5), padx=20)
        
        self.entry_author = ctk.CTkEntry(
            self.frame, 
            placeholder_text="例如: 君泽",
            height=35
        )
        self.entry_author.pack(fill="x", pady=(0, 20), padx=20)
        
        # 帮助提示
        help_text = ctk.CTkLabel(
            self,
            text="💡 提示：可在「微信公众平台 → 设置 → 开发设置」中找到这些信息\n稍后可在「账号配置」中修改",
            font=ctk.CTkFont(size=11),
            text_color="#666666"
        )
        help_text.pack(pady=(10, 5))
        
        # 按钮区域
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=30, pady=(10, 30))
        
        # 跳过按钮
        self.skip_btn = ctk.CTkButton(
            btn_frame,
            text="暂时跳过",
            fg_color="#555555",
            hover_color="#666666",
            height=40,
            command=self.skip_setup
        )
        self.skip_btn.pack(side="left", expand=True, fill="x", padx=(0, 5))
        
        # 完成配置按钮
        self.save_btn = ctk.CTkButton(
            btn_frame,
            text="完成配置",
            fg_color="#E6C35C",
            text_color="black",
            hover_color="#D4B04C",
            height=40,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self.complete_setup
        )
        self.save_btn.pack(side="left", expand=True, fill="x", padx=(5, 0))
        
    def skip_setup(self):
        """跳过配置向导"""
        result = tkinter.messagebox.askyesno(
            "跳过配置",
            "跳过配置后将无法使用发布功能。\n\n您可以随时在「账号配置」中进行设置。\n\n确定要跳过吗？",
            icon='warning'
        )
        if result:
            # 创建空配置文件
            config_path = path_utils.get_external_path("config.json")
            empty_config = {
                "app_id": "",
                "app_secret": "",
                "author_name": "作者",
                "use_proxy": 0
            }
            try:
                with open(config_path, "w", encoding="utf-8") as f:
                    json.dump(empty_config, f, indent=4)
                print("[系统] 已跳过配置向导")
            except Exception as e:
                print(f"[错误] 创建配置文件失败: {e}")
            
            self.destroy()
    
    def complete_setup(self):
        """完成配置"""
        app_id = self.entry_appid.get().strip()
        app_secret = self.entry_secret.get().strip()
        author_name = self.entry_author.get().strip()
        
        # 验证必填项
        if not app_id or not app_secret:
            tkinter.messagebox.showwarning(
                "配置不完整",
                "AppID 和 AppSecret 是必填项！\n\n如果暂时不需要发布功能，可以点击「暂时跳过」。"
            )
            return
        
        # 保存配置
        new_config = {
            "app_id": app_id,
            "app_secret": app_secret,
            "author_name": author_name if author_name else "作者",
            "use_proxy": 0
        }
        
        try:
            config_path = path_utils.get_external_path("config.json")
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(new_config, f, indent=4, ensure_ascii=False)
            
            # 更新父窗口配置
            self.parent.config_data = new_config
            publisher.CONFIG = new_config
            publisher.APP_ID = new_config["app_id"]
            publisher.APP_SECRET = new_config["app_secret"]
            publisher.DEFAULT_AUTHOR = new_config["author_name"]
            
            print(f"[系统] 配置已保存！(保存至: {config_path})")
            
            tkinter.messagebox.showinfo(
                "配置成功",
                "🎉 配置完成！\n\n您现在可以开始使用 Writer Studio 了。"
            )
            
            self.destroy()
        except Exception as e:
            print(f"[错误] 保存配置失败: {e}")
            tkinter.messagebox.showerror(
                "保存失败",
                f"配置保存失败：{str(e)}\n\n请检查文件权限后重试。"
            )

class SettingsWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("配置管理")
        self.geometry("400x380")
        self.resizable(False, False)
        self.attributes("-topmost", True)
        self.label = ctk.CTkLabel(self, text="账号与偏好设置", font=ctk.CTkFont(size=16, weight="bold"))
        self.label.pack(pady=(20, 20))
        self.frame = ctk.CTkFrame(self, fg_color="transparent")
        self.frame.pack(padx=20, fill="x")
        ctk.CTkLabel(self.frame, text="AppID:", anchor="w").pack(fill="x", pady=(5, 0))
        self.entry_appid = ctk.CTkEntry(self.frame, placeholder_text="wx...")
        self.entry_appid.pack(fill="x", pady=(0, 10))
        if parent.config_data.get("app_id"): self.entry_appid.insert(0, parent.config_data.get("app_id"))
        ctk.CTkLabel(self.frame, text="AppSecret:", anchor="w").pack(fill="x", pady=(5, 0))
        self.entry_secret = ctk.CTkEntry(self.frame, show="*", placeholder_text="密钥")
        self.entry_secret.pack(fill="x", pady=(0, 10))
        if parent.config_data.get("app_secret"): self.entry_secret.insert(0, parent.config_data.get("app_secret"))
        ctk.CTkLabel(self.frame, text="默认作者名:", anchor="w").pack(fill="x", pady=(5, 0))
        self.entry_author = ctk.CTkEntry(self.frame, placeholder_text="例如: 君泽")
        self.entry_author.pack(fill="x", pady=(0, 20))
        if parent.config_data.get("author_name"): self.entry_author.insert(0, parent.config_data.get("author_name"))
        self.save_btn = ctk.CTkButton(self, text="保存并关闭", fg_color="#2E8B57", hover_color="#226640", height=40, command=self.save_config)
        self.save_btn.pack(pady=20, padx=20, fill="x", side="bottom")

    def save_config(self):
        new_config = {
            "app_id": self.entry_appid.get().strip(),
            "app_secret": self.entry_secret.get().strip(),
            "author_name": self.entry_author.get().strip(),
            "use_proxy": self.parent.proxy_switch.get()
        }
        try:
            config_path = path_utils.get_external_path("config.json")
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(new_config, f, indent=4)
            self.parent.config_data = new_config
            publisher.CONFIG = new_config
            publisher.APP_ID = new_config["app_id"]
            publisher.APP_SECRET = new_config["app_secret"]
            publisher.DEFAULT_AUTHOR = new_config["author_name"]
            print(f"[系统] 配置已更新！(保存至: {config_path})")
            self.destroy()
        except Exception as e:
            print(f"[错误] 保存失败: {e}")

class WriterStudioApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Writer Studio - 随时上场")
        self.geometry("750x620")
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.config_data = self.load_config()
        self.custom_feature_path = None
        
        # 检查是否需要显示首次配置向导
        self.check_first_run() 

        self.sidebar_frame = ctk.CTkFrame(self, width=180, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(5, weight=1)  # 增加一行
        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="Writer Studio", font=ctk.CTkFont(size=22, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(30, 30))
        self.settings_btn = ctk.CTkButton(self.sidebar_frame, text="账号配置 (Setting)", fg_color="#444", hover_color="#555", command=self.open_settings)
        self.settings_btn.grid(row=1, column=0, padx=20, pady=10)
        self.proxy_switch = ctk.CTkSwitch(self.sidebar_frame, text="启用代理", font=ctk.CTkFont(size=12))
        self.proxy_switch.grid(row=2, column=0, padx=20, pady=20)
        if self.config_data.get("use_proxy"): self.proxy_switch.select()
        self.proxy_switch.configure(command=self.quick_save_proxy)

        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        self.main_label = ctk.CTkLabel(self.main_frame, text="工作流控制台", font=ctk.CTkFont(size=18, weight="bold"))
        self.main_label.pack(pady=10, anchor="w")
        
        # 添加快速编辑器按钮
        self.btn_editor = ctk.CTkButton(
            self.main_frame, 
            text="✏️ 快速编辑器（粘贴飞书/Notion内容）", 
            fg_color="#E6C35C",
            text_color="black",
            hover_color="#D4B04C",
            height=35,
            command=self.open_editor
        )
        self.btn_editor.pack(fill="x", pady=(10, 5))
        
        self.btn_import = ctk.CTkButton(self.main_frame, text="[+] 导入文章包 (.zip / .md)", fg_color="#3B8ED0", hover_color="#36719F", height=35, command=self.import_file)
        self.btn_import.pack(fill="x", pady=(5, 0))
        self.file_entry = ctk.CTkEntry(self.main_frame, placeholder_text="文件名将自动填入...", height=40)
        self.file_entry.pack(fill="x", pady=(5, 10))

        self.feature_frame = ctk.CTkFrame(self.main_frame, fg_color="#2b2b2b")
        self.feature_frame.pack(fill="x", pady=(10, 20))
        self.feature_label = ctk.CTkLabel(self.feature_frame, text="扉页配图: 默认 (几何图形)", anchor="w", text_color="#aaa")
        self.feature_label.pack(side="left", padx=15, pady=10)
        self.btn_reset_feature = ctk.CTkButton(self.feature_frame, text="重置", width=60, fg_color="#555", hover_color="#666", command=self.reset_feature_image)
        self.btn_reset_feature.pack(side="right", padx=(5, 10), pady=10)
        self.btn_select_feature = ctk.CTkButton(self.feature_frame, text="选择图片", width=80, fg_color="#444", hover_color="#555", command=self.select_feature_image)
        self.btn_select_feature.pack(side="right", padx=0, pady=10)

        self.btn_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.btn_frame.pack(fill="x", pady=0)
        self.btn_gen = ctk.CTkButton(self.btn_frame, text="Step 1: 生成黑金排版", height=50, fg_color="#E6C35C", text_color="black", hover_color="#D4B04C", font=ctk.CTkFont(size=15, weight="bold"), command=self.run_generation_thread)
        self.btn_gen.pack(side="left", expand=True, fill="x", padx=(0, 10))
        self.btn_pub = ctk.CTkButton(self.btn_frame, text="Step 2: 发布到微信", height=50, fg_color="#2E8B57", hover_color="#226640", font=ctk.CTkFont(size=15, weight="bold"), command=self.run_publish_thread)
        self.btn_pub.pack(side="left", expand=True, fill="x", padx=(10, 0))
        self.log_label = ctk.CTkLabel(self.main_frame, text="运行日志:", anchor="w", text_color="gray")
        self.log_label.pack(pady=(20, 5), anchor="w")
        self.textbox = ctk.CTkTextbox(self.main_frame, width=400)
        self.textbox.pack(fill="both", expand=True)
        self.textbox.configure(font=("Menlo", 12))
        sys.stdout = TextRedirector(self.textbox)
        print("[系统] 就绪。")
        
        self.editor_window = None
    
    def check_first_run(self):
        """检查是否首次运行，如果是则显示配置向导"""
        config_path = path_utils.get_external_path("config.json")
        
        # 检查配置文件是否存在
        if not os.path.exists(config_path):
            print("[系统] 检测到首次运行，启动配置向导...")
            self.after(500, self.show_setup_wizard)
            return
        
        # 检查配置是否完整（必需的 app_id 和 app_secret）
        if not self.config_data.get("app_id") or not self.config_data.get("app_secret"):
            print("[系统] 检测到配置不完整，启动配置向导...")
            self.after(500, self.show_setup_wizard)
            return
    
    def show_setup_wizard(self):
        """显示配置向导"""
        SetupWizard(self)

    def open_editor(self, force_reload=False):
        """打开富文本编辑器"""
        current_file = self.file_entry.get().strip()
        if self.editor_window is None or not self.editor_window.winfo_exists():
            self.editor_window = RichTextEditor(self, initial_filename=current_file)
            self.editor_window.focus()
        else:
            if force_reload and current_file:
                self.editor_window.reload_with_file(current_file)
            self.editor_window.focus()

    def load_config(self):
        try:
            config_path = path_utils.get_external_path("config.json")
            print(f"[调试] 尝试读取配置: {config_path}")
            if os.path.exists(config_path):
                with open(config_path, "r", encoding="utf-8") as f: return json.load(f)
            return {}
        except Exception as e:
            print(f"[错误] 读取配置失败: {e}")
            return {}
    def open_settings(self):
        if self.settings_window is None or not self.settings_window.winfo_exists(): self.settings_window = SettingsWindow(self) 
        else: self.settings_window.focus() 
    settings_window = None
    def quick_save_proxy(self):
        self.config_data["use_proxy"] = bool(self.proxy_switch.get())
        try:
            with open("config.json", "w", encoding="utf-8") as f: json.dump(self.config_data, f, indent=4)
            publisher.USE_PROXY = self.config_data["use_proxy"]
            print(f"[系统] 代理状态已切换: {'开启' if publisher.USE_PROXY else '关闭'}")
        except: pass

    def select_feature_image(self):
        file_path = filedialog.askopenfilename(title="选择扉页配图", filetypes=[("Images", "*.png *.jpg *.jpeg")])
        if file_path:
            self.custom_feature_path = file_path
            name = os.path.basename(file_path)
            self.feature_label.configure(text=f"扉页配图: {name}", text_color="#E6C35C")
            print(f"[设置] 已选择: {name}")

    def reset_feature_image(self):
        self.custom_feature_path = None
        self.feature_label.configure(text="扉页配图: 默认 (几何图形)", text_color="#aaa")
        print(f"[设置] 已重置为默认。")

    def import_file(self):
        file_path = filedialog.askopenfilename(title="选择文章文件", filetypes=[("Supported files", "*.zip *.md"), ("Zip Package", "*.zip"), ("Markdown", "*.md")])
        if not file_path: return
        try:
            if not os.path.exists("input"): 
                os.makedirs("input")
            
            filename = os.path.basename(file_path)
            target_md_file = None
            
            if filename.lower().endswith(".zip"):
                print(f"[处理] 解压: {filename} ...")
                with zipfile.ZipFile(file_path, 'r') as zip_ref:
                    for file_info in zip_ref.infolist():
                        origin_name = file_info.filename
                        try: fixed_name = origin_name.encode('cp437').decode('utf-8')
                        except: 
                            try: fixed_name = origin_name.encode('cp437').decode('gbk')
                            except: fixed_name = origin_name
                        if fixed_name.startswith("__MACOSX") or fixed_name.startswith("._"): continue
                        
                        lower = fixed_name.lower()
                        # 检查是否是图片或md
                        if lower.endswith(('.png','.jpg','.jpeg','.gif','.md')):
                            file_info.filename = fixed_name
                            zip_ref.extract(file_info, "input")
                            if lower.endswith(".md"): target_md_file = fixed_name
                
                if target_md_file:
                    name_no_ext = os.path.splitext(os.path.basename(target_md_file))[0]
                    self.file_entry.delete(0, "end")
                    self.file_entry.insert(0, name_no_ext)
                    print(f"[成功] 导入完成，已同步到编辑器。")
                    # 自动打开编辑器
                    self.open_editor(force_reload=True)
            else:
                shutil.copy(file_path, os.path.join("input", filename))
                name_no_ext = os.path.splitext(filename)[0]
                self.file_entry.delete(0, "end")
                self.file_entry.insert(0, name_no_ext)
                print(f"[成功] 导入完成，已同步到编辑器。")
                # 自动打开编辑器
                self.open_editor(force_reload=True)
                
        except Exception as e:
            print(f"[错误] 导入失败: {e}")

    def run_generation_thread(self):
        threading.Thread(target=self.run_generation, daemon=True).start()

    def run_generation(self):
        self.btn_gen.configure(state="disabled", text="生成中...")
        
        # 如果编辑器处于打开状态，先触发静默保存
        # 1. 检查编辑器状态和草稿
        draft_file = "input/.draft_autosave.md"
        use_draft = False
        
        # 情况A: 编辑器开着 -> 强制保存
        if self.editor_window and self.editor_window.winfo_exists():
            print("[系统] 检测到编辑器已打开，正在同步内容...")
            if not self.editor_window.save_to_disk_silent():
                print("[错误] 同步保存失败 (可能是文件名为空)，请检查编辑器。")
                self.btn_gen.configure(state="normal", text="Step 1: 生成黑金排版")
                return
            time.sleep(0.2) # 等待IO
            
        # 情况B: 编辑器关了，但有草稿 -> 询问是否使用
        elif os.path.exists(draft_file):
            try:
                # 检查草稿是否为空
                with open(draft_file, 'r', encoding='utf-8') as f: d_content = f.read().strip()
                
                if d_content:
                    # 获取目标文件当前内容用于对比（可选），这里直接询问
                    result = tkinter.messagebox.askyesno(
                        "发现未保存的草稿", 
                        "检测到有未保存的编辑内容（草稿），是否使用该版本进行排版？\n\n选择「是」：使用草稿内容（并将覆盖原文件）\n选择「否」：使用磁盘上的原文件",
                        icon='question'
                    )
                    if result:
                        use_draft = True
            except: pass
            
        # 如果决定使用草稿，覆盖目标文件
        target_name = self.file_entry.get().strip()
        if use_draft and target_name:
             try:
                 with open(draft_file, 'r', encoding='utf-8') as f: content = f.read()
                 target_path = os.path.join("input", f"{target_name}.md")
                 with open(target_path, 'w', encoding='utf-8') as f: f.write(content)
                 print(f"[系统] 已应用草稿内容到: {target_name}.md")
             except Exception as e:
                 print(f"[错误] 应用草稿失败: {e}")

        # 获取用户输入的文件名
        target_name = self.file_entry.get().strip()
        if not target_name:
            print("[错误] 请先输入或导入文章文件名")
            self.btn_gen.configure(state="normal", text="Step 1: 生成黑金排版")
            return
            
        target_filename = f"{target_name}.md"
        
        try:
            print("\n--- 准备环境 ---")
            if not os.path.exists("input"): os.makedirs("input")
            
            # 1. 强力清空：删除 input 目录下所有图片文件
            for f in os.listdir("input"):
                if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                    os.remove(os.path.join("input", f))
            
            # 2. 决定本次的 feature 图片名
            current_feature_name = None 
            if self.custom_feature_path and os.path.exists(self.custom_feature_path):
                ext = os.path.splitext(self.custom_feature_path)[1]
                unique_name = f"feature_{int(time.time())}{ext}"
                target_path = os.path.join("input", unique_name)
                shutil.copy(self.custom_feature_path, target_path)
                current_feature_name = unique_name
                print(f"[处理] 应用自定义配图: {unique_name}")
            
            app.set_specific_feature(current_feature_name)
            
            print(f"--- 开始生成排版: {target_filename} ---")
            # 核心修改：只让 app.py 处理这一个文件！
            app.run_generator(target_filename)
            print("--- 完成 ---")
            
            # 自动打开预览
            preview_html = os.path.join("output", target_name, f"PREVIEW_{target_name}.html")
            if os.path.exists(preview_html):
                print(f"[预览] 正在打开预览页面...")
                os.system(f"open '{preview_html}'")  # macOS 用 open 命令
                
                # 弹窗询问是否发布
                time.sleep(0.5)  # 稍微延迟，确保生成流程完全结束
                result = tkinter.messagebox.askyesno(
                    "预览确认", 
                    "排版生成完成！\n\n预览已打开，请检查排版效果。\n\n确认无误后，是否立即发布到微信公众号？",
                    icon='question'
                )
                if result:
                    print("[用户] 选择立即发布")
                    # 直接调用发布流程
                    threading.Thread(target=self.run_publish, daemon=True).start()
                else:
                    print("[用户] 稍后手动发布")
                    
        except Exception as e:
            print(f"[错误] {e}")
        self.btn_gen.configure(state="normal", text="Step 1: 生成黑金排版")

    def run_publish_thread(self):
        threading.Thread(target=self.run_publish, daemon=True).start()
    def run_publish(self):
        target = self.file_entry.get().strip()
        author = self.config_data.get("author_name", "君泽")
        if not target or not self.config_data.get("app_id"):
            print("[错误] 信息不全")
            self.btn_pub.configure(state="normal", text="Step 2: 发布到微信")
            return
        self.btn_pub.configure(state="disabled", text="上传中...")
        try:
            print(f"\n--- 开始发布: {target} ---")
            publisher.run_publisher(target, author)
            print("--- 完成 ---")
        except Exception as e:
            print(f"[错误] {e}")
        self.btn_pub.configure(state="normal", text="Step 2: 发布到微信")

class TextRedirector(object):
    def __init__(self, widget): self.widget = widget
    def write(self, str_data):
        clean = ''.join(c for c in str_data if ord(c) <= 0xFFFF)
        if clean:
            self.widget.configure(state="normal")
            self.widget.insert("end", clean)
            self.widget.see("end")
            self.widget.configure(state="disabled")
    def flush(self): pass

if __name__ == "__main__":
    app_gui = WriterStudioApp()
    app_gui.mainloop()