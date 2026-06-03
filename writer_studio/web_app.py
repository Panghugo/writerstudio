import os
from functools import wraps

from flask import Flask, jsonify, render_template, request, send_from_directory
from flask_cors import CORS

from . import web_services
from .config import TEMP_BASE_DIR, load_server_config
from .file_safety import get_session_paths, safe_child_path, sanitize_name
from .logging_setup import configure_logging


def create_app():
    flask_app = Flask(
        __name__,
        static_folder='../static',
        template_folder='../templates',
    )
    CORS(flask_app, resources={
        r"/api/*": {"origins": ["http://localhost:5001", "http://127.0.0.1:5001"]}
    })
    configure_logging(flask_app)
    os.makedirs(TEMP_BASE_DIR, exist_ok=True)
    register_routes(flask_app)
    return flask_app


def register_routes(flask_app):
    def json_api(handler):
        """统一处理 JSON API 路由的异常映射：
        ValueError→400，FileNotFoundError→404，其余→500。
        被装饰函数直接返回结果 dict，由装饰器负责 jsonify。"""
        @wraps(handler)
        def wrapper(*args, **kwargs):
            try:
                return jsonify(handler(*args, **kwargs))
            except ValueError as e:
                return error_response(flask_app, e, 400)
            except FileNotFoundError as e:
                return error_response(flask_app, e, 404)
            except Exception as e:
                return error_response(flask_app, e, 500)
        return wrapper

    @flask_app.route('/')
    def index():
        config = load_server_config()
        return render_template('index.html', config=config)

    @flask_app.route('/api/save_and_generate', methods=['POST'])
    @json_api
    def save_and_generate():
        data = request.get_json(silent=True) or {}
        return web_services.generate_preview(data)

    @flask_app.route('/api/generate_social_image', methods=['POST'])
    @json_api
    def generate_social_image():
        data = request.get_json(silent=True) or {}
        return web_services.generate_social_image(data)

    @flask_app.route('/api/publish', methods=['POST'])
    @json_api
    def publish():
        data = request.get_json(silent=True) or {}
        return web_services.publish_wechat(data)

    @flask_app.route('/api/save_config', methods=['POST'])
    def save_config():
        return jsonify({"status": "success", "message": "Settings saved locally (Legacy)."})

    @flask_app.route('/output/<path:session_id>/<path:filename>/<path:filepath>')
    def serve_output_session(session_id, filename, filepath):
        _, output_dir = get_session_paths(session_id)
        target_dir = safe_child_path(output_dir, sanitize_name(filename, 'untitled'))
        return send_from_directory(target_dir, filepath)

    @flask_app.route('/api/upload_image', methods=['POST'])
    def upload_image():
        if 'file' not in request.files:
            return jsonify({'error': 'No file part'}), 400

        try:
            filename = web_services.save_uploaded_image(
                request.files['file'],
                request.form.get('session_id', ''),
                request.form.get('is_feature', '') == 'true',
            )
            return jsonify({'status': 'success', 'filename': filename})
        except ValueError as e:
            return jsonify({'error': str(e)}), 400

    @flask_app.route('/api/remove_feature_image', methods=['POST'])
    @json_api
    def remove_feature_image():
        data = request.get_json(silent=True) or {}
        return web_services.remove_feature_image(data)

    @flask_app.route('/api/publish_blog', methods=['POST'])
    @json_api
    def publish_blog():
        data = request.get_json(silent=True) or {}
        return web_services.publish_blog(data)

    @flask_app.route('/api/open_output_folder', methods=['POST'])
    @json_api
    def open_output_folder():
        data = request.get_json(silent=True) or {}
        return web_services.open_output_folder(data)

    @flask_app.route('/api/list_obsidian_files', methods=['GET'])
    @json_api
    def list_obsidian_files():
        return {"status": "success", "files": web_services.list_obsidian_files()}

    @flask_app.route('/api/load_obsidian_file', methods=['POST'])
    @json_api
    def load_obsidian_file():
        data = request.get_json(silent=True) or {}
        obsidian_file = web_services.load_obsidian_file(data)
        return {
            "status": "success",
            "content": obsidian_file["content"],
            "filename": obsidian_file["filename"],
        }


def error_response(flask_app, error, status_code):
    if status_code >= 500:
        flask_app.logger.exception(error)
    return jsonify({"status": "error", "message": str(error)}), status_code
