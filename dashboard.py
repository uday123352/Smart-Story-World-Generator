"""
Dashboard Routes
================
User profile, stats, AI history, notifications.
"""
from flask import Blueprint, request, jsonify, session
from werkzeug.security import generate_password_hash

dashboard_bp = Blueprint('dashboard', __name__)


def db():
    from flask import current_app
    from database.db_init import get_db
    return get_db(current_app)


# ── Dashboard Stats ───────────────────────────────────────────────────────────
@dashboard_bp.route('/stats', methods=['GET'])
def stats():
    uid = session.get('user_id')
    if not uid:
        return jsonify({'error': 'Login required.'}), 401
    conn = db()

    world_count   = conn.execute("SELECT COUNT(*) FROM worlds     WHERE user_id=?", (uid,)).fetchone()[0]
    char_count    = conn.execute(
        "SELECT COUNT(*) FROM characters c JOIN worlds w ON c.world_id=w.id WHERE w.user_id=?", (uid,)
    ).fetchone()[0]
    story_count   = conn.execute(
        "SELECT COUNT(*) FROM stories s JOIN worlds w ON s.world_id=w.id WHERE w.user_id=?", (uid,)
    ).fetchone()[0]
    total_likes   = conn.execute(
        "SELECT COALESCE(SUM(likes),0) FROM worlds WHERE user_id=?", (uid,)
    ).fetchone()[0]
    recent_worlds = conn.execute(
        "SELECT id,world_name,genre,created_at FROM worlds WHERE user_id=? ORDER BY created_at DESC LIMIT 5",
        (uid,)
    ).fetchall()
    ai_history = conn.execute(
        "SELECT prompt,result_type,created_at FROM ai_history WHERE user_id=? ORDER BY created_at DESC LIMIT 10",
        (uid,)
    ).fetchall()

    conn.close()
    return jsonify({
        'world_count':   world_count,
        'char_count':    char_count,
        'story_count':   story_count,
        'total_likes':   total_likes,
        'recent_worlds': [dict(r) for r in recent_worlds],
        'ai_history':    [dict(r) for r in ai_history],
    }), 200


# ── Update Profile ────────────────────────────────────────────────────────────
@dashboard_bp.route('/profile', methods=['PUT'])
def update_profile():
    uid = session.get('user_id')
    if not uid:
        return jsonify({'error': 'Login required.'}), 401
    data = request.get_json(silent=True) or {}
    bio  = str(data.get('bio', ''))[:300]
    conn = db()
    conn.execute("UPDATE users SET bio=? WHERE id=?", (bio, uid))
    conn.commit()
    conn.close()
    return jsonify({'success': True}), 200
