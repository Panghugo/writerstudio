import json
import os


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_FILE = os.path.join(BASE_DIR, 'web_server.log')
ERROR_LOG_FILE = os.path.join(BASE_DIR, 'web_server_error.log')

LOCAL_INPUT_DIR = os.path.join(BASE_DIR, 'input')
LOCAL_OUTPUT_DIR = os.path.join(BASE_DIR, 'output')
TEMP_BASE_DIR = os.path.join(BASE_DIR, 'temp_sessions')
CONFIG_PATH = os.path.join(BASE_DIR, 'config.json')

ALLOWED_IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg'}
ALLOWED_THEMES = {'black_gold', 'tech_blue', 'paper_white', 'vintage_press'}


def load_server_config():
    if not os.path.exists(CONFIG_PATH):
        return {}
    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}
