import sys
import os

def get_base_path():
    """
    Get the base directory for the application.
    - Frozen (PyInstaller): sys._MEIPASS (where resources like fonts are unpacked)
    - Dev: script directory
    """
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS
    else:
        return os.path.dirname(os.path.abspath(__file__))

def get_user_path():
    """
    Get the directory where user data (input/output/config) should be stored.
    - Frozen (macOS .app): The directory containing the .app bundle (or executable)
    - Dev: script directory
    """
    if getattr(sys, 'frozen', False):
        # sys.executable points to .../WriterStudio.app/Contents/MacOS/WriterStudio
        # We want the directory containing WriterStudio.app
        # This logic assumes the structure: /Path/To/WriterStudio.app/Contents/MacOS/WriterStudio
        # So we need to go up 3 levels to get /Path/To/
        return os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(sys.executable))))
    else:
        return os.path.dirname(os.path.abspath(__file__))

def get_internal_path(rel_path):
    """Resolve path for internal resources (bundled files)"""
    return os.path.join(get_base_path(), rel_path)

def get_external_path(rel_path):
    """Resolve path for external user data (config, input, output)"""
    return os.path.join(get_user_path(), rel_path)

def init_config_if_needed():
    """
    首次运行时，如果config.json不存在但打包了config.template.json，
    则将模板复制为config.json
    """
    if getattr(sys, 'frozen', False):
        # 只在打包环境中执行
        user_config_path = get_external_path("config.json")
        template_in_bundle = get_internal_path("config.template.json")
        
        # 如果config.json不存在，但模板存在
        if not os.path.exists(user_config_path) and os.path.exists(template_in_bundle):
            try:
                import shutil
                shutil.copy(template_in_bundle, user_config_path)
                print(f"[初始化] 已从模板创建配置文件: {user_config_path}")
            except Exception as e:
                print(f"[错误] 配置文件初始化失败: {e}")
