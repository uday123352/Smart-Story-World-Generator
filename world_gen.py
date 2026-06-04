"""
AI World Generation Engine
===========================
Calls the Anthropic Claude API in a SINGLE request to generate
the complete world. Falls back to rich procedural generation if
the API is unavailable, so the app always works.
"""

import json
import re
import random
import math
import os


# ── Anthropic API Client ──────────────────────────────────────────────────────
def call_claude(prompt: str, system: str = "", max_tokens: int = 4000) -> str:
    """
    Single call to Anthropic Messages API.
    Raises RuntimeError with a descriptive message on any failure.
    """
    import urllib.request
    import urllib.error

    api_key = os.environ.get('ANTHROPIC_API_KEY', '').strip()
    if not api_key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY is not set. "
            "Add it to your .env file: ANTHROPIC_API_KEY=sk-ant-..."
        )

    payload = json.dumps({
        "model": "claude-sonnet-4-5",
        "max_tokens": max_tokens,
        "system": system,
        "messages": [{"role": "user", "content": prompt}]
    }).encode('utf-8')

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01"
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            body = json.loads(resp.read().decode('utf-8'))
        return body["content"][0]["text"]

    except urllib.error.HTTPError as e:
        try:
            err_body = json.loads(e.read().decode('utf-8'))
            detail = err_body.get('error', {}).get('message', str(e))
        except Exception:
            detail = str(e)
        raise RuntimeError(f"Anthropic API {e.code}: {detail}")

    except urllib.error.URLError as e:
        raise RuntimeError(f"Network error: {e.reason}")

    except (KeyError, IndexError, json.JSONDecodeError) as e:
        raise RuntimeError(f"Unexpected API response format: {e}")

    except Exception as e:
        raise RuntimeError(f"API call failed: {e}")


# ── JSON Extractor ────────────────────────────────────────────────────────────
def safe_json(text: str, default):
    """Robustly extract JSON from Claude responses regardless of formatting."""
    if not text or not isinstance(text, str):
        return default

    text = text.strip()

    # Strip all markdown fence variants
    text = re.sub(r'```(?:json)?\s*', '', text)
    text = re.sub(r'\s*```', '', text)
    text = text.strip()

    # Direct parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Find outermost balanced { } or [ ]
    for open_ch, close_ch in [('{', '}'), ('[', ']')]:
        start = text.find(open_ch)
        if start == -1:
            continue
        depth, in_str, escape = 0, False, False
        for i, ch in enumerate(text[start:], start):
            if escape:
                escape = False
                continue
            if ch == '\\' and in_str:
                escape = True
                continue
            if ch == '"':
                in_str = not in_str
                continue
            if in_str:
                continue
            if ch == open_ch:
                depth += 1
            elif ch == close_ch:
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(text[start:i+1])
                    except json.JSONDecodeError:
                        break

    return default


# ── Fantasy Name Generator ────────────────────────────────────────────────────
def fantasy_name(seed="", suffix=""):
    prefixes = ["Aer","Vel","Mor","Thal","Zar","Eld","Fyr","Kael","Sol","Drak",
                "Lyr","Vor","Nyx","Ash","Bel","Cor","Gal","Hex","Ivar","Jyn"]
    middles  = ["an","or","en","ar","in","oth","el","un","yl","ath",
                "ir","os","ax","em","al","ix","ur","on","ia","eth"]
    endings  = ["ia","us","or","ar","on","ax","is","um","en","ath",
                "yr","el","ion","ara","ius","ean","oth","iel","orn","ast"]
    random.seed(hash(str(seed) + str(suffix)) % 2**32)
    p = random.choice(prefixes)
    m = random.choice(middles) if random.random() > 0.4 else ""
    e = random.choice(endings)
    return (p + m + e).capitalize() + (" " + suffix if suffix else "")


# ── Procedural Fallback World ─────────────────────────────────────────────────
def build_fallback_world(params: dict) -> dict:
    """
    Rich procedural world that requires no API key.
    Used when Claude is unavailable.
    """
    idea   = params.get('idea', 'A magical world')
    genre  = params.get('genre', 'Fantasy')
    theme  = params.get('theme', 'Epic Adventure')
    tone   = params.get('story_tone', 'Epic')
    magic  = params.get('magic_level', 'High')
    n_char = min(int(params.get('character_count', 5)), 6)

    wn = fantasy_name(idea, "")
    kingdoms = [
        {"kingdom_name": fantasy_name(idea,"Kingdom"), "ruler": f"King {fantasy_name(idea+'k','')}", "capital_city": fantasy_name(idea+'c',''), "army_power": random.randint(60,95), "economy_type": random.choice(["Trade","Agriculture","Mining","Magic"]), "flag_colors": "#8b0000,#ffd700", "politics": "Monarchical rule tempered by a council of elders.", "description": f"A proud {genre.lower()} kingdom nestled between ancient mountains and enchanted forests."},
        {"kingdom_name": fantasy_name(idea+"2","Dominion"), "ruler": f"Empress {fantasy_name(idea+'e','')}", "capital_city": fantasy_name(idea+'e','City'), "army_power": random.randint(60,95), "economy_type": random.choice(["Trade","Seafaring","Alchemy","Conquest"]), "flag_colors": "#000080,#c0c0c0", "politics": "Expansionist empire ruled by an iron empress.", "description": "A vast dominion spanning three continents, held together by fear and commerce."},
        {"kingdom_name": fantasy_name(idea+"3","Conclave"), "ruler": f"Archon {fantasy_name(idea+'a','')}", "capital_city": fantasy_name(idea+'m','Spire'), "army_power": random.randint(40,75), "economy_type": "Magic & Knowledge", "flag_colors": "#4b0082,#e0e0ff", "politics": "Governed by an assembly of archmages.", "description": "A hidden realm of scholars and sorcerers, neutral in worldly conflicts."},
        {"kingdom_name": fantasy_name(idea+"4","Reaches"), "ruler": f"Warlord {fantasy_name(idea+'w','')}", "capital_city": fantasy_name(idea+'f','Fortress'), "army_power": random.randint(75,99), "economy_type": "Pillage & Tribute", "flag_colors": "#2d2d2d,#cc3300", "politics": "Might-makes-right warlord confederacy.", "description": "A harsh northern realm of warriors who respect only strength and honour."},
    ]
    characters = [
        {"name": fantasy_name(idea+"hero",""), "role": "Hero", "archetype": "The Chosen One", "powers": f"Mastery of {magic.lower()} magic; extraordinary combat skill", "backstory": f"Born in obscurity, destiny thrust greatness upon them. They carry the weight of {wn}'s last hope.", "relationships": "Mentor: the old sage. Rival: the villain.", "appearance": "Tall, weathered, with eyes that carry ancient sorrow."},
        {"name": fantasy_name(idea+"vil",""), "role": "Villain", "archetype": "The Dark Lord", "powers": "Necromancy, mind domination, command of shadow armies", "backstory": "Once a celebrated hero, betrayed by the very people they fought to protect. Darkness was the answer.", "relationships": "Nemesis of the hero. Commands three lieutenants.", "appearance": "Cloaked in shadow, with eyes like dying stars."},
        {"name": fantasy_name(idea+"sage",""), "role": "Sage", "archetype": "The Mentor", "powers": "Ancient lore, prophecy, elemental ward-casting", "backstory": "Survivor of the last great war, keeper of secrets most have forgotten.", "relationships": "Guide to the hero. Old enemy of the villain.", "appearance": "Ancient beyond reckoning, with a staff carved from the World Tree."},
    ]
    for i in range(n_char - 3):
        roles = ["Warrior","Rogue","Healer","Ranger","Summoner"]
        characters.append({"name": fantasy_name(idea+f"c{i}",""), "role": roles[i % len(roles)], "archetype": "The Companion", "powers": f"Skilled {roles[i%len(roles)].lower()}", "backstory": f"Joined the party by chance, stayed by choice.", "relationships": "Loyal companion to the hero.", "appearance": "Determined eyes, road-worn gear."})

    story_content = (
        f"In the age of {fantasy_name(idea+'age','')}, when the stars still sang and the earth remembered its first name, "
        f"the land of {wn} stood at the edge of reckoning. Three moons hung in the amber sky, "
        f"each one a scar from the war that ended the previous age.\n\n"
        f"The idea that would shake the world began simply: {idea}. "
        f"Few understood its weight. Fewer still had the courage to act. "
        f"Yet in a village whose name the maps had forgotten, one soul stirred from sleep with the taste of destiny on their lips.\n\n"
        f"The ancient prophecy spoke of this: '{wn} shall know its darkest hour before its greatest dawn.' "
        f"The time had come. The journey begins now."
    )

    return {
        "world_name": wn,
        "tagline": f"Where {theme.lower()} meets ancient darkness — {wn} awaits.",
        "description": f"{wn} is a {genre.lower()} world of breathtaking scale and ancient mystery. {theme} defines the era, while forces of light and shadow wage their eternal struggle across continents shaped by forgotten gods.",
        "lore": f"Before time had a name, the Primordial Architects shaped {wn} from raw possibility. They wove magic into the bedrock, breathed consciousness into the elements, and departed — leaving their creation to find its own meaning. Civilizations rose and fell like tides. Each age left its mark: ruins in the deep forests, glyphs on mountain faces, whispers in the wind that speak of things that should not be remembered.",
        "history": f"The First Age saw the rise of the Elder Races, whose cities glittered like earthbound stars. The Second Age brought the Sundering — a catastrophe that reshaped continents and drove the Elder Races into legend. Now in the Third Age, the children of survivors rebuild, unaware that the Sundering was no accident.",
        "magic_system": f"Magic in {wn} flows from the Resonance — an invisible lattice connecting all living things. Those born attuned can draw on it, bending reality through will and word. Magic has a cost: each casting ages the soul slightly. The most powerful mages are ancient beyond their years.",
        "political_system": "Four major powers maintain an uneasy balance: monarchy, empire, arcane conclave, and warlord confederacy. Ancient treaties — crumbling now — keep open war at bay. Spies, assassins, and diplomats wage shadow wars daily.",
        "economy": "Gold and gemstones underpin trade, but magical reagents have become the true currency of power. Alchemical compounds, enchanted goods, and spell components flow along trade routes guarded by mercenaries.",
        "religion": f"The Pantheon of {fantasy_name(idea+'god','')} governs faith across {wn}. Chief among them is the Luminary, god of truth and fire. Their shadow-twin, the Unspoken, draws cultists who seek power through darkness. Most folk worship neither — only the harvest and the hearth.",
        "world_rules": [
            "Magic always demands equal sacrifice — power drawn must be power repaid.",
            "The dead do not rest in places where great evil occurred.",
            "Dragons are not monsters — they are living memory, older than nations.",
            "Names have power; speaking the true name of a thing grants dominion over it.",
            "The stars are the eyes of gods; to curse under open sky is to invite divine attention."
        ],
        "timeline": [
            {"era": "First Age", "year": "0 AE", "event": "The Primordial Architects shape the world and depart."},
            {"era": "Second Age", "year": "1200 AE", "event": "The Sundering — continents fracture, elder races vanish."},
            {"era": "Third Age", "year": "2400 AE", "event": "The Great Rebuilding; current nations are founded."},
            {"era": "Age of Reckoning", "year": "Current", "event": "Ancient seals weaken; the villain stirs; the hero awakens."}
        ],
        "kingdoms": kingdoms,
        "characters": characters,
        "creatures": [
            {"name": fantasy_name(idea+"beast1",""), "species": "Void Wraith", "powers": "Intangibility, fear aura, soul drain", "habitat": "Ruins and battlefields", "lore": "Born where many died in anguish, they hunger for the warmth they can no longer feel.", "danger_level": 9},
            {"name": fantasy_name(idea+"beast2",""), "species": "Stone Drake", "powers": "Petrification breath, armoured hide, tremor-sense", "habitat": "Mountain ranges", "lore": "Ancient guardians of deep-earth treasures, they sleep for centuries between wakenings.", "danger_level": 8},
            {"name": fantasy_name(idea+"beast3",""), "species": "Thornwood Stalker", "powers": "Camouflage, poison barbs, pack coordination", "habitat": "Ancient forests", "lore": "A predator that learned to think — and then learned to plan.", "danger_level": 7},
            {"name": fantasy_name(idea+"beast4",""), "species": "Tide Leviathan", "powers": "Storm summoning, crushing tentacles, depth pressure", "habitat": "Deep ocean", "lore": "Sailors pray it remains asleep. When it dreams, hurricanes form.", "danger_level": 10},
        ],
        "weapons": [
            {"name": fantasy_name(idea+"w1","Blade"), "weapon_type": "Sword", "power_level": 10, "lore": "Forged in the heart of a dying star, it cuts through shadow as easily as flesh.", "owner": characters[0]["name"] if characters else "Unknown"},
            {"name": fantasy_name(idea+"w2","Staff"), "weapon_type": "Staff", "power_level": 9, "lore": "Carved from the World Tree's heartwood; channels magic without cost — at a terrible price.", "owner": characters[2]["name"] if len(characters) > 2 else "Unknown"},
            {"name": fantasy_name(idea+"w3","Crown"), "weapon_type": "Artefact", "power_level": 10, "lore": "Whomever wears it commands absolute loyalty — and absolute corruption follows.", "owner": characters[1]["name"] if len(characters) > 1 else "Unknown"},
            {"name": fantasy_name(idea+"w4","Bow"), "weapon_type": "Bow", "power_level": 8, "lore": "Its arrows never miss what the archer truly intends to strike.", "owner": "The last Ranger-Saint"},
        ],
        "story": {
            "chapter_title": f"Chapter 1: The Awakening of {wn}",
            "content": story_content,
            "dialogues": [
                {"speaker": characters[0]["name"] if characters else "Hero", "line": f"I did not ask for this destiny. But I will not run from it."},
                {"speaker": characters[2]["name"] if len(characters) > 2 else "Sage", "line": f"The seals are breaking. {wn} has hours, not days."},
                {"speaker": characters[1]["name"] if len(characters) > 1 else "Villain", "line": "You cannot stop what has already begun. I have made certain of it."},
            ],
            "quests": [
                {"title": "The Seal of the First Age", "description": "Locate and restore the three ancient seals before the void consumes the land.", "reward": "The blessing of the Primordial Architects — power beyond mortal reckoning."},
                {"title": "The Traitor's Name", "description": "Discover who among the four kingdoms broke the ancient treaty and why.", "reward": "Alliance with the wronged nation and their legendary army."},
            ],
            "plot_twist": f"The villain was once the greatest hero {wn} ever produced — and the hero is their direct descendant."
        },
        "dynamic_events": [
            {"type": "Seal Weakening", "title": "The Northern Seal Cracks", "description": "Void energy bleeds through the weakening barrier; dead walk again in the frozen north.", "affected_kingdom": kingdoms[0]["kingdom_name"], "severity": 9},
            {"type": "Political Crisis", "title": "Succession War Looms", "description": "The emperor's heir has vanished; three claimants ready their armies.", "affected_kingdom": kingdoms[1]["kingdom_name"], "severity": 7},
            {"type": "Dragon Awakening", "title": "Kaeltharion Stirs", "description": "The oldest living dragon ends its century of sleep — and it is angry.", "affected_kingdom": kingdoms[2]["kingdom_name"], "severity": 8},
        ],
        "map_svg": generate_fantasy_map_svg(wn, [k["kingdom_name"] for k in kingdoms]),
        "genre": genre,
        "theme": theme,
        "magic_level": magic,
        "story_tone": tone,
    }


# ── Single-Call Claude World Generation ──────────────────────────────────────
def generate_world(params: dict) -> dict:
    """
    Generates a complete world. Tries Claude API first (single call),
    falls back to rich procedural generation if API unavailable.
    """
    idea    = params.get('idea', 'A magical fantasy world')
    genre   = params.get('genre', 'Fantasy')
    theme   = params.get('theme', 'Epic Adventure')
    wtype   = params.get('world_type', 'Continental')
    magic   = params.get('magic_level', 'High')
    civ     = params.get('civilization_type', 'Medieval')
    tone    = params.get('story_tone', 'Epic')
    n_char  = min(int(params.get('character_count', 5)), 6)
    villain = params.get('villain_type', 'Dark Sorcerer')
    lang    = params.get('language_style', 'Archaic Fantasy')

    # Skip API if no key configured
    api_key = os.environ.get('ANTHROPIC_API_KEY', '').strip()
    if not api_key:
        result = build_fallback_world(params)
        result['_source'] = 'procedural'
        return result

    system = (
        f"You are a master {genre} world-builder. "
        f"Generate rich, imaginative content. Style: {tone} tone, {lang} language. "
        f"Magic: {magic}. Civilization: {civ}. World type: {wtype}. "
        "Return ONLY valid JSON. No markdown fences, no explanatory text."
    )

    prompt = f"""Create a complete {genre} story world based on this idea: "{idea}"

Return a single JSON object with ALL of these keys:

{{
  "world_name": "Unique epic name",
  "tagline": "One evocative sentence",
  "description": "3-paragraph rich description (min 200 words)",
  "lore": "Deep ancient lore (min 150 words)",
  "history": "World history paragraph (min 120 words)",
  "magic_system": "How magic works (min 80 words)",
  "political_system": "Government structures (min 60 words)",
  "economy": "Economic system (min 50 words)",
  "religion": "Primary beliefs (min 60 words)",
  "world_rules": ["Rule 1", "Rule 2", "Rule 3", "Rule 4", "Rule 5"],
  "timeline": [
    {{"era": "Name", "year": "0 AE", "event": "Founding event"}},
    {{"era": "Name", "year": "500 AE", "event": "Major event"}},
    {{"era": "Name", "year": "1000 AE", "event": "Major event"}},
    {{"era": "Current Age", "year": "Now", "event": "Present crisis"}}
  ],
  "kingdoms": [
    {{
      "kingdom_name": "Name", "ruler": "Title Name",
      "capital_city": "City", "army_power": 80,
      "economy_type": "Trade", "flag_colors": "#hex1,#hex2",
      "politics": "One sentence", "description": "Two sentences"
    }},
    {{same for kingdom 2}},
    {{same for kingdom 3}},
    {{same for kingdom 4}}
  ],
  "characters": [
    {{
      "name": "Name", "role": "Hero",
      "archetype": "The Chosen One", "powers": "Power list",
      "backstory": "Two sentences", "relationships": "Relations",
      "appearance": "Brief description"
    }},
    {{"name": "Name", "role": "Villain", "archetype": "{villain}", "powers": "Powers", "backstory": "Two sentences", "relationships": "Relations", "appearance": "Description"}},
    {{"name": "Name", "role": "Sage", "archetype": "Mentor", "powers": "Powers", "backstory": "Two sentences", "relationships": "Relations", "appearance": "Description"}},
    {{"name": "Name", "role": "Warrior", "archetype": "Guardian", "powers": "Powers", "backstory": "Two sentences", "relationships": "Relations", "appearance": "Description"}},
    {{"name": "Name", "role": "Rogue", "archetype": "Trickster", "powers": "Powers", "backstory": "Two sentences", "relationships": "Relations", "appearance": "Description"}}
  ],
  "creatures": [
    {{"name": "Name", "species": "Type", "powers": "Powers", "habitat": "Where", "lore": "One myth sentence", "danger_level": 8}},
    {{"name": "Name", "species": "Type", "powers": "Powers", "habitat": "Where", "lore": "One myth sentence", "danger_level": 7}},
    {{"name": "Name", "species": "Type", "powers": "Powers", "habitat": "Where", "lore": "One myth sentence", "danger_level": 9}},
    {{"name": "Name", "species": "Type", "powers": "Powers", "habitat": "Where", "lore": "One myth sentence", "danger_level": 6}}
  ],
  "weapons": [
    {{"name": "Name", "weapon_type": "Sword", "power_level": 9, "lore": "Origin sentence", "owner": "Who wields it"}},
    {{"name": "Name", "weapon_type": "Staff", "power_level": 8, "lore": "Origin sentence", "owner": "Who wields it"}},
    {{"name": "Name", "weapon_type": "Bow", "power_level": 7, "lore": "Origin sentence", "owner": "Who wields it"}},
    {{"name": "Name", "weapon_type": "Artefact", "power_level": 10, "lore": "Origin sentence", "owner": "Who wields it"}}
  ],
  "story": {{
    "chapter_title": "Chapter 1: [dramatic title]",
    "content": "700-word cinematic opening chapter with atmosphere and action",
    "dialogues": [
      {{"speaker": "Name", "line": "Memorable dialogue"}},
      {{"speaker": "Name", "line": "Memorable dialogue"}},
      {{"speaker": "Name", "line": "Memorable dialogue"}}
    ],
    "quests": [
      {{"title": "Quest name", "description": "Quest description", "reward": "Reward"}},
      {{"title": "Quest name", "description": "Quest description", "reward": "Reward"}}
    ],
    "plot_twist": "One shocking revelation for later"
  }},
  "dynamic_events": [
    {{"type": "War", "title": "Event title", "description": "One dramatic sentence", "affected_kingdom": "Kingdom name", "severity": 8}},
    {{"type": "Magic Storm", "title": "Event title", "description": "One dramatic sentence", "affected_kingdom": "Kingdom name", "severity": 7}},
    {{"type": "Political Crisis", "title": "Event title", "description": "One dramatic sentence", "affected_kingdom": "Kingdom name", "severity": 6}}
  ]
}}"""

    # Single API call — if it fails, use the fallback
    try:
        raw = call_claude(prompt, system, max_tokens=4000)
        world = safe_json(raw, {})
        if not world or 'world_name' not in world:
            raise RuntimeError("Claude returned incomplete data")
    except RuntimeError as e:
        print(f"[WorldGen] Claude unavailable ({e}), using procedural fallback")
        result = build_fallback_world(params)
        result['_source'] = 'procedural'
        return result

    # Ensure all required keys are present (fill gaps from fallback)
    fallback = build_fallback_world(params)
    for key in ('kingdoms', 'characters', 'creatures', 'weapons', 'story',
                'dynamic_events', 'world_rules', 'timeline'):
        if not world.get(key):
            world[key] = fallback[key]

    # Generate SVG map using actual kingdom names
    k_names = [k.get('kingdom_name', '?') for k in (world.get('kingdoms') or [])]
    world['map_svg'] = generate_fantasy_map_svg(world.get('world_name', 'World'), k_names)
    world.setdefault('genre', genre)
    world.setdefault('theme', theme)
    world.setdefault('magic_level', magic)
    world.setdefault('story_tone', tone)
    world['_source'] = 'claude'
    return world


def continue_story(world_name: str, chapter_num: int, previous_content: str) -> dict:
    """Generate the next chapter of an existing story."""
    prompt = f"""Continue the story of "{world_name}". Write chapter {chapter_num}.
Previous chapter summary: {previous_content[:400]}

Return ONLY this JSON:
{{
  "chapter_title": "Chapter {chapter_num}: [dramatic title]",
  "content": "600-word continuation chapter",
  "dialogues": [
    {{"speaker": "Name", "line": "Line"}},
    {{"speaker": "Name", "line": "Line"}}
  ],
  "quests": [{{"title": "Quest", "description": "Description", "reward": "Reward"}}],
  "plot_twist": "New development"
}}"""
    try:
        raw = call_claude(prompt, max_tokens=1800)
        result = safe_json(raw, {})
        if result and 'content' in result:
            return result
    except RuntimeError:
        pass
    return {
        'chapter_title': f'Chapter {chapter_num}: The Story Continues',
        'content': f'The tale of {world_name} continues, each step deeper into the unknown...',
        'dialogues': [],
        'quests': [],
        'plot_twist': ''
    }


# ── SVG Fantasy Map Generator ─────────────────────────────────────────────────
def generate_fantasy_map_svg(world_name: str, kingdoms: list) -> str:
    W, H = 800, 600
    random.seed(hash(world_name) % 2**32)

    land_colors  = ["#2d4a1e","#3a5c26","#4a7a30","#3d5c22","#2a3d18"]
    water_color  = "#0a1628"
    ocean_color  = "#0d1f3c"
    mountain_col = "#6b5b45"
    snow_col     = "#e8e0d0"
    forest_col   = "#1a3a12"

    cx, cy = W // 2, H // 2
    pts = []
    for i in range(24):
        angle = (2 * math.pi * i) / 24
        r = 200 + random.randint(-80, 80)
        pts.append((cx + r * math.cos(angle), cy + r * math.sin(angle) * 0.7))
    land_path = "M " + " L ".join(f"{x:.1f},{y:.1f}" for x, y in pts) + " Z"

    sub_regions = []
    n = max(3, len(kingdoms))
    for i in range(n):
        angle = (2 * math.pi * i) / n
        rx = cx + (120 + random.randint(-40, 40)) * math.cos(angle)
        ry = cy + (90  + random.randint(-30, 30)) * math.sin(angle) * 0.7
        sp = []
        for j in range(8):
            a2 = (2 * math.pi * j) / 8
            r2 = 60 + random.randint(-20, 20)
            sp.append((rx + r2*math.cos(a2), ry + r2*math.sin(a2)*0.8))
        sub_regions.append({
            'cx': rx, 'cy': ry,
            'path': "M " + " L ".join(f"{x:.1f},{y:.1f}" for x,y in sp) + " Z",
            'color': random.choice(land_colors),
            'kingdom': kingdoms[i] if i < len(kingdoms) else fantasy_name(str(i))
        })

    mountains = []
    for _ in range(random.randint(4, 8)):
        mx, my = random.randint(150,650), random.randint(100,500)
        h, w = random.randint(20,40), random.randint(15,30)
        mountains.append(f'<polygon points="{mx},{my} {mx-w},{my+h} {mx+w},{my+h}" fill="{mountain_col}" opacity="0.85"/>'
                         f'<polygon points="{mx},{my+5} {mx-w+5},{my+h} {mx+w-5},{my+h}" fill="{snow_col}" opacity="0.6"/>')

    forests = [f'<circle cx="{random.randint(120,680)}" cy="{random.randint(80,520)}" r="{random.randint(12,25)}" fill="{forest_col}" opacity="0.7"/>'
               for _ in range(random.randint(5,10))]

    rivers = []
    for _ in range(random.randint(2,4)):
        x0,y0 = random.randint(200,600), random.randint(100,250)
        x1,y1 = x0+random.randint(-100,100), y0+random.randint(100,200)
        x2,y2 = x1+random.randint(-60,60), H-50
        rivers.append(f'<path d="M {x0},{y0} Q {x1},{y1} {x2},{y2}" stroke="#1a4a7a" stroke-width="2" fill="none" opacity="0.6"/>')

    def castle(x, y, label):
        x, y = int(x), int(y)
        lbl = str(label)[:14]
        return (f'<rect x="{x-6}" y="{y-10}" width="12" height="10" fill="#ffd700" opacity="0.9"/>'
                f'<rect x="{x-8}" y="{y-14}" width="4" height="6" fill="#ffd700" opacity="0.9"/>'
                f'<rect x="{x-2}" y="{y-14}" width="4" height="6" fill="#ffd700" opacity="0.9"/>'
                f'<rect x="{x+4}" y="{y-14}" width="4" height="6" fill="#ffd700" opacity="0.9"/>'
                f'<text x="{x}" y="{y+14}" font-family="serif" font-size="8" fill="#ffd700" text-anchor="middle" opacity="0.9">{lbl}</text>')

    castles_svg = "".join(castle(r['cx'], r['cy'], r['kingdom']) for r in sub_regions)

    return f"""<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" style="width:100%;height:100%;border-radius:12px">
  <defs>
    <radialGradient id="oceanGrad" cx="50%" cy="50%" r="70%">
      <stop offset="0%" stop-color="{water_color}"/>
      <stop offset="100%" stop-color="{ocean_color}"/>
    </radialGradient>
    <filter id="glow"><feGaussianBlur stdDeviation="3" result="blur"/>
      <feComposite in="SourceGraphic" in2="blur" operator="over"/></filter>
    <pattern id="waves" width="40" height="20" patternUnits="userSpaceOnUse">
      <path d="M0,10 Q10,0 20,10 Q30,20 40,10" stroke="#1a3a6a" stroke-width="0.5" fill="none" opacity="0.3"/>
    </pattern>
  </defs>
  <rect width="{W}" height="{H}" fill="url(#oceanGrad)"/>
  <rect width="{W}" height="{H}" fill="url(#waves)"/>
  <path d="{land_path}" fill="#3a5c26" stroke="#2a4016" stroke-width="2" opacity="0.9"/>
  {"".join(f'<path d="{r["path"]}" fill="{r["color"]}" stroke="#1a2a10" stroke-width="1" opacity="0.7"/>' for r in sub_regions)}
  {"".join(forests)}
  {"".join(rivers)}
  {"".join(mountains)}
  {castles_svg}
  <text x="{W//2}" y="30" font-family="serif" font-size="18" font-weight="bold" fill="#ffd700" text-anchor="middle" filter="url(#glow)">{world_name}</text>
  <g transform="translate(740,540)">
    <circle r="18" fill="#0a1628" stroke="#ffd700" stroke-width="1" opacity="0.8"/>
    <text x="0" y="-8" font-size="8" fill="#ffd700" text-anchor="middle">N</text>
    <text x="0" y="14" font-size="8" fill="#ffd700" text-anchor="middle">S</text>
    <text x="-12" y="3" font-size="8" fill="#ffd700" text-anchor="middle">W</text>
    <text x="12" y="3" font-size="8" fill="#ffd700" text-anchor="middle">E</text>
    <line x1="0" y1="-5" x2="0" y2="5" stroke="#ffd700" stroke-width="1"/>
    <line x1="-5" y1="0" x2="5" y2="0" stroke="#ffd700" stroke-width="1"/>
  </g>
  <rect x="4" y="4" width="{W-8}" height="{H-8}" fill="none" stroke="#ffd700" stroke-width="1.5" opacity="0.3" rx="8"/>
</svg>"""
