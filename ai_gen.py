"""
AI Generation Routes
====================
REST endpoints that trigger AI world generation,
story continuation, and related creative generation tasks.
"""

import json
from flask import Blueprint, request, jsonify, session
from ai_engine.world_gen import generate_world, continue_story

ai_bp = Blueprint('ai', __name__)


# ── Generate World ────────────────────────────────────────────────────────────
@ai_bp.route('/generate-world', methods=['POST'])
def gen_world():
    uid = session.get('user_id')
    if not uid:
        return jsonify({'error': 'Login required.'}), 401

    data   = request.get_json(silent=True) or {}
    params = {
        'idea':               str(data.get('idea', 'A magical fantasy world'))[:500],
        'genre':              str(data.get('genre', 'Fantasy')),
        'theme':              str(data.get('theme', 'Epic Adventure')),
        'world_type':         str(data.get('world_type', 'Continental')),
        'magic_level':        str(data.get('magic_level', 'High')),
        'civilization_type':  str(data.get('civilization_type', 'Medieval')),
        'story_tone':         str(data.get('story_tone', 'Epic')),
        'character_count':    int(data.get('character_count', 5)),
        'villain_type':       str(data.get('villain_type', 'Dark Sorcerer')),
        'language_style':     str(data.get('language_style', 'Archaic Fantasy')),
    }

    # ── Call AI Engine ────────────────────────────────────────────────────────
    try:
        world = generate_world(params)
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'success': False, 'error': f'World generation failed: {e}'}), 500

    # ── Persist to DB ──────────────────────────────────────────────────────────
    from flask import current_app
    from database.db_init import get_db
    conn = get_db(current_app)
    try:
        cur = conn.execute(
            """INSERT INTO worlds
               (user_id, world_name, genre, theme, world_type, magic_level,
                story_tone, lore, plot, history, magic_system,
                political_system, economy, religion, world_rules, timeline,
                map_svg, is_public)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,0)""",
            (
                uid,
                world.get('world_name', 'Unnamed World'),
                params['genre'], params['theme'],
                params['world_type'], params['magic_level'], params['story_tone'],
                world.get('lore', ''), world.get('description', ''),
                world.get('history', ''), world.get('magic_system', ''),
                world.get('political_system', ''), world.get('economy', ''),
                world.get('religion', ''),
                json.dumps(world.get('world_rules', [])),
                json.dumps(world.get('timeline', [])),
                world.get('map_svg', ''),
            )
        )
        world_id = cur.lastrowid

        # Save kingdoms
        for k in world.get('kingdoms', []):
            if not isinstance(k, dict):
                continue
            conn.execute(
                """INSERT INTO kingdoms
                   (world_id,kingdom_name,ruler,capital_city,army_power,
                    economy_type,flag_colors,politics,description)
                   VALUES (?,?,?,?,?,?,?,?,?)""",
                (world_id, k.get('kingdom_name', ''), k.get('ruler', ''),
                 k.get('capital_city', ''), int(k.get('army_power', 50)),
                 k.get('economy_type', ''), k.get('flag_colors', ''),
                 k.get('politics', ''), k.get('description', ''))
            )

        # Save characters
        for c in world.get('characters', []):
            if not isinstance(c, dict):
                continue
            conn.execute(
                """INSERT INTO characters
                   (world_id,name,role,archetype,powers,backstory,
                    relationships,appearance)
                   VALUES (?,?,?,?,?,?,?,?)""",
                (world_id, c.get('name', ''), c.get('role', ''),
                 c.get('archetype', ''), c.get('powers', ''),
                 c.get('backstory', ''), c.get('relationships', ''),
                 c.get('appearance', ''))
            )

        # Save creatures
        for cr in world.get('creatures', []):
            if not isinstance(cr, dict):
                continue
            conn.execute(
                """INSERT INTO creatures
                   (world_id,name,species,powers,habitat,lore,danger_level)
                   VALUES (?,?,?,?,?,?,?)""",
                (world_id, cr.get('name', ''), cr.get('species', ''),
                 cr.get('powers', ''), cr.get('habitat', ''),
                 cr.get('lore', ''), int(cr.get('danger_level', 5)))
            )

        # Save weapons
        for w in world.get('weapons', []):
            if not isinstance(w, dict):
                continue
            conn.execute(
                """INSERT INTO weapons
                   (world_id,name,weapon_type,power_level,lore,owner)
                   VALUES (?,?,?,?,?,?)""",
                (world_id, w.get('name', ''), w.get('weapon_type', ''),
                 int(w.get('power_level', 5)), w.get('lore', ''), w.get('owner', ''))
            )

        # Save opening chapter
        story = world.get('story', {})
        if isinstance(story, dict) and story:
            conn.execute(
                """INSERT INTO stories
                   (world_id,chapter_title,chapter_num,content,dialogues,quests)
                   VALUES (?,?,1,?,?,?)""",
                (world_id, story.get('chapter_title', 'Chapter 1: The Beginning'),
                 story.get('content', ''),
                 json.dumps(story.get('dialogues', [])),
                 json.dumps(story.get('quests', [])))
            )

        # Log AI history
        conn.execute(
            "INSERT INTO ai_history (user_id,prompt,result_type,world_id) VALUES (?,?,?,?)",
            (uid, params['idea'], 'world_generation', world_id)
        )

        conn.commit()
        world['world_id'] = world_id
        return jsonify({'success': True, 'world': world}), 201

    except Exception as e:
        import traceback; traceback.print_exc()
        try:
            conn.rollback()
        except Exception:
            pass
        return jsonify({'success': False, 'error': f'Database error: {e}'}), 500
    finally:
        conn.close()


# ── Continue Story ────────────────────────────────────────────────────────────
@ai_bp.route('/continue-story/<int:world_id>', methods=['POST'])
def api_continue_story(world_id):
    uid = session.get('user_id')
    if not uid:
        return jsonify({'error': 'Login required.'}), 401

    from flask import current_app
    from database.db_init import get_db
    conn = get_db(current_app)

    try:
        world = conn.execute(
            "SELECT * FROM worlds WHERE id=? AND user_id=?", (world_id, uid)
        ).fetchone()
        if not world:
            return jsonify({'error': 'World not found.'}), 404

        chapters = conn.execute(
            "SELECT COUNT(*) as cnt FROM stories WHERE world_id=?", (world_id,)
        ).fetchone()
        chapter_num = (chapters['cnt'] or 0) + 1

        last = conn.execute(
            "SELECT content FROM stories WHERE world_id=? ORDER BY chapter_num DESC LIMIT 1",
            (world_id,)
        ).fetchone()
        prev = last['content'] if last else ''

        try:
            new_chapter = continue_story(world['world_name'], chapter_num, prev)
        except Exception as e:
            import traceback; traceback.print_exc()
            return jsonify({'success': False, 'error': str(e)}), 500

        conn.execute(
            """INSERT INTO stories
               (world_id,chapter_title,chapter_num,content,dialogues,quests)
               VALUES (?,?,?,?,?,?)""",
            (world_id,
             new_chapter.get('chapter_title', f'Chapter {chapter_num}'),
             chapter_num,
             new_chapter.get('content', ''),
             json.dumps(new_chapter.get('dialogues', [])),
             json.dumps(new_chapter.get('quests', [])))
        )
        conn.commit()
        return jsonify({'success': True, 'chapter': new_chapter}), 201

    except Exception as e:
        import traceback; traceback.print_exc()
        try:
            conn.rollback()
        except Exception:
            pass
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        conn.close()
