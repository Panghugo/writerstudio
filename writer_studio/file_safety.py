import os
import re

from .config import LOCAL_INPUT_DIR, LOCAL_OUTPUT_DIR, TEMP_BASE_DIR


def sanitize_session_id(session_id):
    safe_id = ''.join([c for c in (session_id or '') if c.isalnum() or c in '-_'])
    return safe_id or ''


def sanitize_name(value, default='untitled'):
    """Keep user-visible Chinese names while preventing filesystem traversal."""
    name = os.path.basename((value or '').strip())
    name = re.sub(r'[\\/:*?"<>|\x00-\x1f]', '_', name).strip('. ')
    return name[:120] or default


def safe_child_path(base_dir, *parts):
    base = os.path.abspath(base_dir)
    target = os.path.abspath(os.path.join(base, *parts))
    if os.path.commonpath([base, target]) != base:
        raise ValueError('Invalid path')
    return target


def is_under_any(path, roots):
    target = os.path.abspath(path)
    for root in roots:
        base = os.path.abspath(root)
        try:
            if os.path.commonpath([base, target]) == base:
                return True
        except ValueError:
            continue
    return False


def get_session_paths(session_id):
    """Get input/output directories for a specific session."""
    if not session_id:
        return LOCAL_INPUT_DIR, LOCAL_OUTPUT_DIR

    safe_id = sanitize_session_id(session_id)
    base = os.path.join(TEMP_BASE_DIR, safe_id)
    return os.path.join(base, 'input'), os.path.join(base, 'output')
