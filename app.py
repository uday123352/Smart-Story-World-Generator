"""
AI Smart Story World Generator - Main Flask Application
======================================================
Entry point for the backend server. Initializes the Flask app,
registers blueprints, sets up the database, and configures sessions.
"""

import os
import sys
import secrets
from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS

# ── Ensure project root is on sys.path so all packages resolve ───────────────
_BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_DIR = os.path.dirname(_BACKEND_DIR)
for _p in [_BACKEND_DIR, _PROJECT_DIR]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from database.db_init import init_db

# ── App Factory ─────────────────────────────────────────────────────────────
def create_app():
    app = Flask(
        __name__,
        static_folder=os.path.join(os.path.dirname(__file__), '..', 'frontend'),
        template_folder=os.path.join(os.path.dirname(__file__), 'templates')
    )

    # ── Configuration ────────────────────────────────────────────────────────
    # CRITICAL: SECRET_KEY must be stable across restarts or sessions break.
    # Read from env first; fall back to a file-persisted key so it survives restarts.
    secret_key = os.environ.get('SECRET_KEY')
    if not secret_key:
        key_file = os.path.join(_PROJECT_DIR, '.secret_key')
        if os.path.exists(key_file):
            with open(key_file, 'r') as f:
                secret_key = f.read().strip()
        if not secret_key:
            secret_key = secrets.token_hex(32)
            try:
                with open(key_file, 'w') as f:
                    f.write(secret_key)
            except OSError:
                pass  # read-only fs, that's ok

    app.config['SECRET_KEY'] = secret_key
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['PERMANENT_SESSION_LIFETIME'] = 86400 * 30  # 30 days
    app.config['DATABASE'] = os.path.join(
        os.path.dirname(__file__), '..', 'database', 'storyworld.db'
    )
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload

    # ── CORS ─────────────────────────────────────────────────────────────────
    CORS(app, supports_credentials=True, origins=[
        'http://localhost:5000',
        'http://127.0.0.1:5000',
        'http://0.0.0.0:5000',
    ])

    # ── Database Init ─────────────────────────────────────────────────────────
    with app.app_context():
        init_db(app)

    # ── Blueprints ────────────────────────────────────────────────────────────
    from routes.auth import auth_bp
    from routes.worlds import worlds_bp
    from routes.ai_gen import ai_bp
    from routes.dashboard import dashboard_bp

    app.register_blueprint(auth_bp,      url_prefix='/api/auth')
    app.register_blueprint(worlds_bp,    url_prefix='/api/worlds')
    app.register_blueprint(ai_bp,        url_prefix='/api/ai')
    app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')

    # ── Static Frontend Routes ────────────────────────────────────────────────
    frontend_dir = os.path.join(os.path.dirname(__file__), '..', 'frontend')

    @app.route('/')
    def index():
        return send_from_directory(frontend_dir, 'index.html')

    @app.route('/login')
    def login_page():
        return send_from_directory(frontend_dir, 'login.html')

    @app.route('/signup')
    def signup_page():
        return send_from_directory(frontend_dir, 'signup.html')

    @app.route('/dashboard')
    def dashboard_page():
        return send_from_directory(frontend_dir, 'dashboard.html')

    @app.route('/favicon.ico')
    def favicon():
        # Return 204 No Content instead of 404 to stop browser error spam
        return '', 204

    @app.route('/<path:filename>')
    def static_files(filename):
        return send_from_directory(frontend_dir, filename)

    # ── Global Error Handlers ─────────────────────────────────────────────────
    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({'error': 'Bad request', 'detail': str(e)}), 400

    @app.errorhandler(401)
    def unauthorized(e):
        return jsonify({'authenticated': False, 'error': 'Unauthorized'}), 401

    @app.errorhandler(403)
    def forbidden(e):
        return jsonify({'error': 'Forbidden'}), 403

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({'error': 'Resource not found'}), 404

    @app.errorhandler(500)
    def server_error(e):
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Internal server error', 'detail': str(e)}), 500

    return app


# ── Entry Point ───────────────────────────────────────────────────────────────
if __name__ == '__main__':
    app = create_app()
    print("🌍 AI Story World Generator running at http://127.0.0.1:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
