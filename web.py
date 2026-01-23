

import os
import json
import time
import shutil
import logging
from logging.handlers import RotatingFileHandler
import uuid
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
import app
import publisher
import blog_publisher
import path_utils

# Configure logging with rotation
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(BASE_DIR, 'web_server.log')
ERROR_LOG_FILE = os.path.join(BASE_DIR, 'web_server_error.log')

# Configure main log with rotation (10MB max, keep 3 backups)
log_handler = RotatingFileHandler(
    LOG_FILE,
    maxBytes=10 * 1024 * 1024,  # 10MB
    backupCount=3
)
log_handler.setLevel(logging.INFO)
log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
log_handler.setFormatter(log_formatter)

# Configure error log with rotation
error_handler = RotatingFileHandler(
    ERROR_LOG_FILE,
    maxBytes=10 * 1024 * 1024,  # 10MB
    backupCount=3
)
error_handler.setLevel(logging.ERROR)
error_handler.setFormatter(log_formatter)

# Set up root logger
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
root_logger.addHandler(log_handler)
root_logger.addHandler(error_handler)

# Also log to console for launchd
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(log_formatter)
root_logger.addHandler(console_handler)

# Initialize Flask
app_server = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app_server)  # Enable CORS for GitHub Pages frontend

# Configure Flask's logger to use our handlers
app_server.logger.handlers = root_logger.handlers
app_server.logger.setLevel(logging.INFO)

# Configure paths (BASE_DIR already defined above for logging)
# Legacy local paths for fallback
LOCAL_INPUT_DIR = os.path.join(BASE_DIR, 'input')
LOCAL_OUTPUT_DIR = os.path.join(BASE_DIR, 'output')
CONFIG_PATH = os.path.join(BASE_DIR, 'config.json')

# Session Storage (In a real SaaS, use Redis/S3. Here we use local temp folders)
TEMP_BASE_DIR = os.path.join(BASE_DIR, 'temp_sessions')
os.makedirs(TEMP_BASE_DIR, exist_ok=True)

def get_session_paths(session_id):
    """Get input/output directories for a specific session."""
    if not session_id: return LOCAL_INPUT_DIR, LOCAL_OUTPUT_DIR
    
    # Sanitize session_id to prevent traversal
    safe_id = "".join([c for c in session_id if c.isalnum() or c in "-_"])
    base = os.path.join(TEMP_BASE_DIR, safe_id)
    return os.path.join(base, 'input'), os.path.join(base, 'output')

# --- Routes ---

@app_server.route('/')
def index():
    """Render the main editor page."""
    # Load config for initial state (Optional: Remove this in Phase 2 for full security)
    config = {}
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                config = json.load(f)
        except: pass
        
    return render_template('index.html', config=config)

@app_server.route('/api/save_and_generate', methods=['POST'])
def save_and_generate():
    """Save markdown content and trigger generation."""
    try:
        data = request.json
        filename = data.get('filename', 'untitled').strip()
        session_id = data.get('session_id', '').strip()
        theme = data.get('theme', 'black_gold').strip() # Get theme
        author_name = data.get('author_name', '作者').strip() # Get author name
        if not filename: filename = 'untitled'
        content = data.get('content', '')
        
        # Get Session Paths
        input_dir, output_dir = get_session_paths(session_id)
        os.makedirs(input_dir, exist_ok=True)
        os.makedirs(output_dir, exist_ok=True)
        
        # Save Markdown
        md_file = f"{filename}.md"
        md_path = os.path.join(input_dir, md_file)
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(content)
            
        # Run Generator
        print(f"Generating for: {md_file} (Session: {session_id}, Theme: {theme}, Author: {author_name})")
        # Call app.main with isolated paths, theme, and author name
        app.main(target_md=md_file, input_dir=input_dir, output_dir=output_dir, theme=theme, author_name=author_name)
        
        # Find the preview HTML
        output_folder = os.path.join(output_dir, filename)
        preview_html_path = None
        if os.path.exists(output_folder):
            for f in os.listdir(output_folder):
                if f.startswith("PREVIEW_") and f.endswith(".html"):
                    preview_html_path = f
                    break
        
        if preview_html_path:
            # URL now includes session_id
            preview_url = f"/output/{session_id}/{filename}/{preview_html_path}"
            return jsonify({"status": "success", "preview_url": preview_url, "message": "Generated successfully!"})
        else:
            return jsonify({"status": "warning", "message": "Generation completed but preview file not found."})

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500

@app_server.route('/api/publish', methods=['POST'])
def publish():
    """Publish draft to WeChat."""
    try:
        data = request.json
        filename = data.get('filename', '').strip()
        session_id = data.get('session_id', '').strip()
        
        # Client-Side Credentials
        app_id = data.get('app_id', '').strip()
        app_secret = data.get('app_secret', '').strip()
        author_name = data.get('author_name', '').strip()
        
        if not filename:
             return jsonify({"status": "error", "message": "Filename is required"}), 400
        if not app_id or not app_secret:
             return jsonify({"status": "error", "message": "Missing WeChat AppID or AppSecret. Please configure in Settings."}), 400

        # Run Publisher
        # Use Isolated Output Directory
        _, output_dir = get_session_paths(session_id)
        
        # We need to capture stdout/print from publisher to return to user?
        # For now, we rely on exception handling.
        # Initialize with explicit credentials
        uploader = publisher.WeChatPublisher(app_id, app_secret)
        uploader.publish_draft(filename, author_name, base_output_dir=output_dir)
        
        return jsonify({"status": "success", "message": "Draft published to WeChat!"})

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500

@app_server.route('/api/save_config', methods=['POST'])
def save_config():
    """Save configuration."""
    # TODO: In Phase 2, we stop saving to disk.
    return jsonify({"status": "success", "message": "Settings saved locally (Legacy)."})

@app_server.route('/output/<path:session_id>/<path:filename>/<path:filepath>')
def serve_output_session(session_id, filename, filepath):
    """Serve files from session storage."""
    # e.g. /output/session_123/article1/PREVIEW_...
    _, output_dir = get_session_paths(session_id)
    target_dir = os.path.join(output_dir, filename)
    return send_from_directory(target_dir, filepath)

@app_server.route('/api/upload_image', methods=['POST'])
def upload_image():
    """Handle image upload."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
        
    session_id = request.form.get('session_id', '')
    is_feature = request.form.get('is_feature', '') == 'true'
    input_dir, _ = get_session_paths(session_id)
    os.makedirs(input_dir, exist_ok=True)
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
        
    if file:
        # If this is a feature image, rename it to feature.png/jpg
        if is_feature:
            # Get file extension
            ext = os.path.splitext(file.filename)[1].lower()
            if ext not in ['.png', '.jpg', '.jpeg']:
                ext = '.png'  # Default to PNG
            filename = f'feature{ext}'
        else:
            filename = file.filename
            
        file.save(os.path.join(input_dir, filename))
        return jsonify({'status': 'success', 'filename': filename})

import threading

@app_server.route('/api/publish_blog', methods=['POST'])
def publish_blog():
    """Publish to local Next.js Blog and Deploy to Vercel."""
    try:
        data = request.json
        content = data.get('content', '')
        filename = data.get('filename', 'Untitled').strip()
        if not filename: filename = 'Untitled'
        author = data.get('author_name', 'Hugo')
        
        # 1. Write file locally
        path = blog_publisher.publish_to_blog(filename, content, author)
        
        # 2. Trigger GitHub Sync in Background
        def run_deploy():
            blog_publisher.deploy_to_github(commit_message=f"Post: {filename}")
            
        threading.Thread(target=run_deploy).start()
        
        return jsonify({
            "status": "success", 
            "message": f"Saved to {path}. 🚀 Syncing to GitHub...", 
            "path": path
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500

# --- Obsidian Integration ---

@app_server.route('/api/list_obsidian_files', methods=['GET'])
def list_obsidian_files():
    """List all Markdown files in the Obsidian vault folder."""
    try:
        # Load config
        if not os.path.exists(CONFIG_PATH):
            return jsonify({"status": "error", "message": "配置文件不存在"}), 404
        
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        vault_path = config.get('obsidian_vault_path', '')
        if not vault_path or not os.path.exists(vault_path):
            return jsonify({"status": "error", "message": "Obsidian 文件夹路径未配置或不存在"}), 404
        
        # List all .md files
        files = []
        for filename in os.listdir(vault_path):
            if filename.endswith('.md') and not filename.startswith('.'):
                filepath = os.path.join(vault_path, filename)
                stat = os.stat(filepath)
                files.append({
                    'name': filename,
                    'size': stat.st_size,
                    'modified': stat.st_mtime,
                    'modified_str': time.strftime('%Y-%m-%d %H:%M', time.localtime(stat.st_mtime))
                })
        
        # Sort by modified time (newest first)
        files.sort(key=lambda x: x['modified'], reverse=True)
        
        return jsonify({"status": "success", "files": files})
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500

@app_server.route('/api/load_obsidian_file', methods=['POST'])
def load_obsidian_file():
    """Load a specific Obsidian file and process images."""
    try:
        data = request.json
        filename = data.get('filename', '').strip()
        session_id = data.get('session_id', '').strip()
        
        if not filename:
            return jsonify({"status": "error", "message": "文件名不能为空"}), 400
        
        # Load config
        if not os.path.exists(CONFIG_PATH):
            return jsonify({"status": "error", "message": "配置文件不存在"}), 404
        
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        vault_path = config.get('obsidian_vault_path', '')
        if not vault_path or not os.path.exists(vault_path):
            return jsonify({"status": "error", "message": "Obsidian 文件夹路径未配置或不存在"}), 404
        
        # Security: prevent directory traversal
        if '..' in filename or '/' in filename or '\\' in filename:
            return jsonify({"status": "error", "message": "非法文件名"}), 400
        
        filepath = os.path.join(vault_path, filename)
        if not os.path.exists(filepath):
            return jsonify({"status": "error", "message": "文件不存在"}), 404
        
        # Read file content
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Process Obsidian image references
        content = process_obsidian_images(content, vault_path, session_id)
        
        # Extract filename without extension for default naming
        base_filename = os.path.splitext(filename)[0]
        
        return jsonify({
            "status": "success",
            "content": content,
            "filename": base_filename
        })
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500

def process_obsidian_images(content, vault_path, session_id=''):
    """Process Obsidian image references and copy images to input directory."""
    import re
    
    # Get session paths
    input_dir, _ = get_session_paths(session_id)
    os.makedirs(input_dir, exist_ok=True)
    
    # Pattern for Obsidian image references: ![[image.png]]
    pattern = r'!\[\[([^\]]+\.(png|jpg|jpeg|gif|webp|svg))\]\]'
    
    def replace_image(match):
        image_name = match.group(1)
        
        # Try to find the image in vault directory or attachments folder
        possible_paths = [
            os.path.join(vault_path, image_name),
            os.path.join(vault_path, 'attachments', image_name),
            os.path.join(vault_path, 'assets', image_name),
        ]
        
        source_path = None
        for path in possible_paths:
            if os.path.exists(path):
                source_path = path
                break
        
        if source_path:
            # Copy image to input directory
            dest_path = os.path.join(input_dir, os.path.basename(image_name))
            try:
                shutil.copy2(source_path, dest_path)
                # Return standard Markdown format
                return f'![{os.path.splitext(image_name)[0]}]({os.path.basename(image_name)})'
            except Exception as e:
                logging.error(f"Failed to copy image {image_name}: {e}")
                return match.group(0)  # Keep original if copy fails
        else:
            logging.warning(f"Image not found: {image_name}")
            return match.group(0)  # Keep original if not found
    
    # Replace all Obsidian image references
    processed_content = re.sub(pattern, replace_image, content, flags=re.IGNORECASE)
    
    return processed_content

if __name__ == '__main__':
    print("✅ 已加载本地配置 (config.json)")
    print("🚀 Writer Studio Web Server (Cloud Mode) starting at http://localhost:5001")
    app_server.run(host='0.0.0.0', port=5001, debug=True)
