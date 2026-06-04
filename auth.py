"""
Authentication Routes
=====================
Handles user signup, login, logout, and session validation.
Uses Werkzeug's secure password hashing. All inputs are validated
and sanitized before database interaction.
"""

import re
import sqlite3
from flask import Blueprint, request, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash

auth_bp = Blueprint('auth', __name__)

# ── Helper ────────────────────────────────────────────────────────────────────
def get_db():
    from flask import current_app
    from database.db_init import get_db as _get_db
    return _get_db(current_app)


def validate_email(email: str) -> bool:
    return bool(re.match(r'^[\w\.-]+@[\w\.-]+\.\w{2,}$', email))


def validate_username(username: str) -> bool:
    return bool(re.match(r'^[a-zA-Z0-9_]{3,20}$', username))


# ── Signup ────────────────────────────────────────────────────────────────────
@auth_bp.route('/signup', methods=['POST'])
def signup():
    data = request.get_json(silent=True) or {}

    username = str(data.get('username', '')).strip()
    email    = str(data.get('email', '')).strip().lower()
    password = str(data.get('password', ''))
    confirm  = str(data.get('confirm_password', ''))

    # ── Validation ────────────────────────────────────────────────────────────
    errors = []
    if not validate_username(username):
        errors.append('Username must be 3–20 alphanumeric characters or underscores.')
    if not validate_email(email):
        errors.append('Invalid email address.')
    if len(password) < 8:
        errors.append('Password must be at least 8 characters.')
    if password != confirm:
        errors.append('Passwords do not match.')
    if errors:
        return jsonify({'success': False, 'errors': errors}), 400

    pw_hash = generate_password_hash(password)

    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
            (username, email, pw_hash)
        )
        conn.commit()
        row = conn.execute(
            "SELECT id, username, email FROM users WHERE email = ?", (email,)
        ).fetchone()
        session.permanent = True
        session['user_id']  = row['id']
        session['username'] = row['username']
        return jsonify({'success': True, 'user': {'id': row['id'], 'username': row['username']}}), 201
    except sqlite3.IntegrityError as e:
        field = 'email' if 'email' in str(e) else 'username'
        return jsonify({'success': False, 'errors': [f'That {field} is already taken.']}), 409
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'success': False, 'errors': ['Server error, please try again.']}), 500
    finally:
        conn.close()


# ── Login ─────────────────────────────────────────────────────────────────────
@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json(silent=True) or {}

    identifier = str(data.get('identifier', '')).strip()   # email or username
    password   = str(data.get('password', ''))
    remember   = bool(data.get('remember', False))

    if not identifier or not password:
        return jsonify({'success': False, 'errors': ['All fields are required.']}), 400

    conn = get_db()
    try:
        row = conn.execute(
            "SELECT * FROM users WHERE email = ? OR username = ?",
            (identifier.lower(), identifier)
        ).fetchone()

        if not row or not check_password_hash(row['password_hash'], password):
            return jsonify({'success': False, 'errors': ['Invalid credentials.']}), 401

        session.permanent = remember
        session['user_id']  = row['id']
        session['username'] = row['username']

        return jsonify({
            'success': True,
            'user': {'id': row['id'], 'username': row['username'], 'email': row['email']}
        }), 200
    finally:
        conn.close()


# ── Logout ────────────────────────────────────────────────────────────────────
@auth_bp.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': True, 'message': 'Logged out.'}), 200


# ── Session Check ─────────────────────────────────────────────────────────────
@auth_bp.route('/me', methods=['GET'])
def me():
    uid = session.get('user_id')
    if not uid:
        return jsonify({'authenticated': False}), 401

    conn = get_db()
    try:
        row = conn.execute(
            "SELECT id, username, email, avatar, bio, created_at FROM users WHERE id = ?",
            (uid,)
        ).fetchone()
        if not row:
            session.clear()
            return jsonify({'authenticated': False}), 401
        user = {
            'id':         row['id'],
            'username':   row['username'],
            'email':      row['email'],
            'avatar':     row['avatar'] if row['avatar'] else 'default',
            'bio':        row['bio'] if row['bio'] else '',
            'created_at': row['created_at'],
        }
        return jsonify({'authenticated': True, 'user': user}), 200
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'authenticated': False, 'error': str(e)}), 500
    finally:
        conn.close()
