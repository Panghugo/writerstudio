#!/usr/bin/env python3
# 快速编辑器测试 - 完全使用tkinter

import tkinter as tk
from tkinter import filedialog, messagebox, Text, END, INSERT
from PIL import Image, ImageTk
import os

class SimpleEditor(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("快速编辑器测试")
        self.geometry("800x600")
        self.configure(bg="#1e1e1e")
        
        # 顶部提示
        top_frame = tk.Frame(self, bg="#2b2b2b", height=50)
        top_frame.pack(fill="x", padx=10, pady=10)
        
        label = tk.Label(
            top_frame,
            text="提示: 直接打字或粘贴文字，点击按钮添加图片",
            bg="#2b2b2b",
            fg="#E6C35C",
            font=("PingFang SC", 12)
        )
        label.pack(side="left", padx=10, pady=10)
        
        add_btn = tk.Button(
            top_frame,
            text="添加图片",
            bg="#555",
            fg="white",
            command=self.add_image
        )
        add_btn.pack(side="right", padx=10, pady=10)
        
        # Text编辑器
        self.text = Text(
            self,
            wrap="word",
            font=("PingFang SC", 14),
            bg="#2b2b2b",
            fg="#ffffff",
            insertbackground="#E6C35C",
            selectbackground="#4a4a4a",
            padx=15,
            pady=15
        )
        self.text.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 添加初始文字
        self.text.insert("1.0", "在这里输入或粘贴文字...\n\n测试能否打字和粘贴。")
        
        # 底部按钮
        bottom_frame = tk.Frame(self, bg="#1e1e1e")
        bottom_frame.pack(fill="x", padx=10, pady=10)
        
        self.filename_entry = tk.Entry(bottom_frame, width=30, bg="#2b2b2b", fg="white")
        self.filename_entry.pack(side="left", padx=5)
        
        save_btn = tk.Button(
            bottom_frame,
            text="保存",
            bg="#E6C35C",
            fg="black",
            command=self.save_content
        )
        save_btn.pack(side="left", padx=5)
        
        # 获取焦点
        self.text.focus_set()
        self.images = []
        self.image_counter = 0
    
    def add_image(self):
        file_path = filedialog.askopenfilename(
            title="选择图片",
            filetypes=[("图片文件", "*.png *.jpg *.jpeg *.gif")]
        )
        if not file_path:
            return
        
        try:
            img = Image.open(file_path)
            self.image_counter += 1
            img_filename = f"pasted_image_{self.image_counter}.png"
            img_path = os.path.join("input", img_filename)
            os.makedirs("input", exist_ok=True)
            img.save(img_path)
            
            # 显示缩略图
            display_img = img.copy()
            display_img.thumbnail((500, 300), Image.LANCZOS)
            photo = ImageTk.PhotoImage(display_img)
            self.images.append(photo)
            
            self.text.insert(INSERT, "\n")
            self.text.image_create(INSERT, image=photo)
            self.text.insert(INSERT, f"\n![图片]({img_filename})\n\n")
            print(f"图片已添加: {img_filename}")
        except Exception as e:
            messagebox.showerror("错误", f"添加图片失败：{str(e)}")
    
    def save_content(self):
        filename = self.filename_entry.get().strip()
        if not filename:
            messagebox.showwarning("提示", "请输入文件名")
            return
        
        content = self.text.get("1.0", END).strip()
        md_path = os.path.join("input", f"{filename}.md")
        
        try:
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(content)
            messagebox.showinfo("成功", f"已保存到: {md_path}")
            print(f"文件已保存: {md_path}")
        except Exception as e:
            messagebox.showerror("错误", f"保存失败：{str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口
    
    editor = SimpleEditor(root)
    
    root.mainloop()
