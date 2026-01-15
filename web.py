

import os
import json
import time
import shutil
import logging
import uuid
from flask import Flask, render_template, request, jsonify, send_from_directory
import app
import publisher
import path_utils

# Initialize Flask
app_server = Flask(__name__, static_folder='static', template_folder='templates')

# Configure paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
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
        print(f"Generating for: {md_file} (Session: {session_id})")
        # Call app.main with isolated paths
        app.main(target_md=md_file, input_dir=input_dir, output_dir=output_dir)
        
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
    input_dir, _ = get_session_paths(session_id)
    os.makedirs(input_dir, exist_ok=True)
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
        
    if file:
        filename = file.filename
        file.save(os.path.join(input_dir, filename))
        return jsonify({'status': 'success', 'filename': filename})

if __name__ == '__main__':
    print("🚀 Writer Studio Web Server (Cloud Mode) starting at http://localhost:5001")
    app_server.run(host='0.0.0.0', port=5001, debug=True)
