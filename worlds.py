"""
Worlds Routes
=============
CRUD for saved worlds, community gallery, likes, comments.
"""
import json
from flask import Blueprint, request, jsonify, session

worlds_bp = Blueprint('worlds', __name__)


def db():
    from flask import current_app
    from database.db_init import get_db
    return get_db(current_app)


# ── List user's worlds ────────────────────────────────────────────────────────
@worlds_bp.route('/', methods=['GET'])
def list_worlds():
    uid = session.get('user_id')
    if not uid:
        return jsonify({'error': 'Login required.'}), 401
    conn = db()
    try:
        rows = conn.execute(
            "SELECT id,world_name,genre,theme,magic_level,story_tone,likes,is_public,created_at "
            "FROM worlds WHERE user_id=? ORDER BY created_at DESC", (uid,)
        ).fetchall()
        return jsonify({'worlds': [dict(r) for r in rows]}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


# ── Get single world (full) ───────────────────────────────────────────────────
@worlds_bp.route('/<int:world_id>', methods=['GET'])
def get_world(world_id):
    uid = session.get('user_id')
    conn = db()
    world = conn.execute("SELECT * FROM worlds WHERE id=?", (world_id,)).fetchone()
    if not world:
        conn.close()
        return jsonify({'error': 'Not found.'}), 404
    w = dict(world)
    if w['user_id'] != uid and not w['is_public']:
        conn.close()
        return jsonify({'error': 'Forbidden.'}), 403

    w['kingdoms']   = [dict(r) for r in conn.execute("SELECT * FROM kingdoms   WHERE world_id=?", (world_id,)).fetchall()]
    w['characters'] = [dict(r) for r in conn.execute("SELECT * FROM characters WHERE world_id=?", (world_id,)).fetchall()]
    w['creatures']  = [dict(r) for r in conn.execute("SELECT * FROM creatures  WHERE world_id=?", (world_id,)).fetchall()]
    w['weapons']    = [dict(r) for r in conn.execute("SELECT * FROM weapons    WHERE world_id=?", (world_id,)).fetchall()]
    w['stories']    = [dict(r) for r in conn.execute(
        "SELECT * FROM stories WHERE world_id=? ORDER BY chapter_num", (world_id,)
    ).fetchall()]
    w['comments']   = [dict(r) for r in conn.execute(
        """SELECT c.*, u.username FROM comments c
           JOIN users u ON c.user_id=u.id
           WHERE c.world_id=? ORDER BY c.created_at DESC""", (world_id,)
    ).fetchall()]

    conn.close()

    # Parse JSON fields
    for field in ['world_rules', 'timeline']:
        if w.get(field) and isinstance(w[field], str):
            try:
                w[field] = json.loads(w[field])
            except Exception:
                pass

    return jsonify({'world': w}), 200


# ── Delete world ──────────────────────────────────────────────────────────────
@worlds_bp.route('/<int:world_id>', methods=['DELETE'])
def delete_world(world_id):
    uid = session.get('user_id')
    if not uid:
        return jsonify({'error': 'Login required.'}), 401
    conn = db()
    conn.execute("DELETE FROM worlds WHERE id=? AND user_id=?", (world_id, uid))
    conn.commit()
    conn.close()
    return jsonify({'success': True}), 200


# ── Toggle public ─────────────────────────────────────────────────────────────
@worlds_bp.route('/<int:world_id>/toggle-public', methods=['POST'])
def toggle_public(world_id):
    uid = session.get('user_id')
    if not uid:
        return jsonify({'error': 'Login required.'}), 401
    conn = db()
    row = conn.execute("SELECT is_public FROM worlds WHERE id=? AND user_id=?",
                       (world_id, uid)).fetchone()
    if not row:
        conn.close()
        return jsonify({'error': 'Not found.'}), 404
    new_val = 0 if row['is_public'] else 1
    conn.execute("UPDATE worlds SET is_public=? WHERE id=?", (new_val, world_id))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'is_public': bool(new_val)}), 200


# ── Like world ────────────────────────────────────────────────────────────────
@worlds_bp.route('/<int:world_id>/like', methods=['POST'])
def like_world(world_id):
    conn = db()
    conn.execute("UPDATE worlds SET likes=likes+1 WHERE id=?", (world_id,))
    conn.commit()
    row = conn.execute("SELECT likes FROM worlds WHERE id=?", (world_id,)).fetchone()
    conn.close()
    return jsonify({'likes': row['likes'] if row else 0}), 200


# ── Add comment ───────────────────────────────────────────────────────────────
@worlds_bp.route('/<int:world_id>/comment', methods=['POST'])
def add_comment(world_id):
    uid = session.get('user_id')
    if not uid:
        return jsonify({'error': 'Login required.'}), 401
    data    = request.get_json(silent=True) or {}
    content = str(data.get('content', '')).strip()[:500]
    if not content:
        return jsonify({'error': 'Comment is empty.'}), 400
    conn = db()
    conn.execute("INSERT INTO comments (world_id,user_id,content) VALUES (?,?,?)",
                 (world_id, uid, content))
    conn.commit()
    conn.close()
    return jsonify({'success': True}), 201


# ── Community gallery ─────────────────────────────────────────────────────────
@worlds_bp.route('/community', methods=['GET'])
def community():
    conn = db()
    rows = conn.execute(
        """SELECT w.id,w.world_name,w.genre,w.theme,w.magic_level,
                  w.likes,w.created_at,u.username
           FROM worlds w JOIN users u ON w.user_id=u.id
           WHERE w.is_public=1
           ORDER BY w.likes DESC, w.created_at DESC
           LIMIT 50"""
    ).fetchall()
    conn.close()
    return jsonify({'worlds': [dict(r) for r in rows]}), 200
