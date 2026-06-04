# ⚔ WorldForge AI — AI Smart Story World Generator

> **Create infinite fantasy worlds from a single idea using AI.**
> Generate kingdoms, characters, maps, lore, quests, and cinematic stories instantly.

---

## ✨ Features

| Category | What's Generated |
|---|---|
| 🌍 **World Overview** | Name, lore, history, magic system, political system, economy, religion, world rules |
| 🏰 **Kingdoms** | Names, rulers, capitals, army power, politics, flag colors, culture |
| 👤 **Characters** | Heroes, villains, side characters, backstories, powers, relationships |
| 🗺 **Interactive Map** | Procedural SVG fantasy map with mountains, rivers, forests, castles, kingdoms |
| 📖 **Story Engine** | Cinematic chapters, dialogues, quests, plot twists — continuable with AI |
| 🐉 **Creatures** | Unique mythical beasts with powers, habitats, danger levels, lore |
| ⚔ **Weapons** | Legendary weapons with origin stories, power levels, owners |
| ⚡ **Dynamic Events** | Wars, dragon attacks, magic storms, political revolutions |
| 📅 **Timeline** | Ages and eras of world history |

---

## 🛠 Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | HTML5, CSS3 (Glassmorphism + Dark Fantasy), Vanilla JS |
| **Backend** | Python 3 + Flask |
| **Database** | SQLite |
| **AI Engine** | Anthropic Claude API (`claude-sonnet-4-20250514`) |
| **Maps** | Procedural SVG generation (no external service needed) |

---

## 📁 Project Structure

```
ai-story-world-generator/
├── frontend/
│   ├── index.html          ← Cinematic homepage
│   ├── login.html          ← Login page
│   ├── signup.html         ← Registration page
│   ├── dashboard.html      ← AI generator + user dashboard
│   ├── style.css           ← Master dark fantasy stylesheet
│   └── app.js              ← Frontend JS (particles, nav, auth)
│
├── backend/
│   ├── app.py              ← Flask application factory & entry point
│   ├── requirements.txt    ← Python dependencies
│   ├── routes/
│   │   ├── auth.py         ← Signup, login, logout, session
│   │   ├── worlds.py       ← CRUD, community, likes, comments
│   │   ├── ai_gen.py       ← AI world generation endpoints
│   │   └── dashboard.py    ← Stats, profile
│   ├── ai_engine/
│   │   └── world_gen.py    ← Claude API calls + SVG map generator
│   └── models/             ← (reserved for ORM models)
│
├── database/
│   └── storyworld.db       ← SQLite database (auto-created)
│
├── run.sh                  ← macOS/Linux setup & launch
├── run.bat                 ← Windows setup & launch
└── README.md
```

---

## 🚀 Quick Start

### Prerequisites
- **Python 3.9+** → [python.org](https://python.org)
- **Anthropic API Key** → [console.anthropic.com](https://console.anthropic.com)

---

### macOS / Linux

```bash
# 1. Clone or unzip the project
cd ai-story-world-generator

# 2. Set your API key
export ANTHROPIC_API_KEY=sk-ant-your-key-here

# 3. Run the setup script
chmod +x run.sh
./run.sh
```

### Windows

```bat
REM 1. Open Command Prompt in the project folder
REM 2. Set your API key
set ANTHROPIC_API_KEY=sk-ant-your-key-here

REM 3. Double-click run.bat  OR  run from cmd:
run.bat
```

### Manual Setup (any OS)

```bash
# 1. Create virtual environment
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r backend/requirements.txt

# 3. Set API key
export ANTHROPIC_API_KEY=sk-ant-your-key-here

# 4. Run the server
cd backend
python app.py
```

Then open **http://127.0.0.1:5000** in your browser.

---

## 🗄 Database Schema

```sql
users       (id, username, email, password_hash, avatar, bio, created_at)
worlds      (id, user_id, world_name, genre, theme, lore, map_svg, ...)
characters  (id, world_id, name, role, powers, backstory, relationships)
kingdoms    (id, world_id, kingdom_name, ruler, army_power, politics, ...)
stories     (id, world_id, chapter_title, chapter_num, content, dialogues)
creatures   (id, world_id, name, species, powers, danger_level, ...)
weapons     (id, world_id, name, weapon_type, power_level, lore, owner)
ai_history  (id, user_id, prompt, result_type, world_id, created_at)
comments    (id, world_id, user_id, content, created_at)
```

---

## 🔒 Security Features

- ✅ **Password hashing** — Werkzeug `generate_password_hash` (PBKDF2-SHA256)
- ✅ **Session management** — Flask server-side sessions with secret key
- ✅ **SQL injection prevention** — Parameterized queries throughout
- ✅ **Input validation** — Server-side regex validation on all user inputs
- ✅ **CORS** — Restricted to localhost in development
- ✅ **Foreign key constraints** — SQLite `PRAGMA foreign_keys = ON`
- ✅ **XSS prevention** — Frontend `escHtml()` on all dynamic content

---

## 🎨 Design System

| Token | Value |
|---|---|
| Primary font | Cinzel Decorative (display) + EB Garamond (body) |
| Gold accent | `#c9a227` |
| Background | `#050811` (void) → `#0d1424` (cards) |
| Effects | Glassmorphism, particle canvas, neon glow, floating islands |
| Animations | CSS keyframes, Intersection Observer scroll reveal |

---

## ⚙️ Configuration

Environment variables:

| Variable | Required | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | **Yes** | Your Claude API key |
| `SECRET_KEY` | No | Flask session secret (auto-generated if unset) |

---

## 🗺 API Endpoints

### Auth
| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/auth/signup` | Register new user |
| POST | `/api/auth/login` | Login |
| POST | `/api/auth/logout` | Logout |
| GET  | `/api/auth/me` | Get current session |

### AI Generation
| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/ai/generate-world` | Generate full world from parameters |
| POST | `/api/ai/continue-story/<world_id>` | Generate next story chapter |

### Worlds
| Method | Endpoint | Description |
|---|---|---|
| GET  | `/api/worlds/` | List user's worlds |
| GET  | `/api/worlds/<id>` | Get world detail (full) |
| DELETE | `/api/worlds/<id>` | Delete world |
| POST | `/api/worlds/<id>/toggle-public` | Toggle public/private |
| POST | `/api/worlds/<id>/like` | Like a world |
| POST | `/api/worlds/<id>/comment` | Add comment |
| GET  | `/api/worlds/community` | Public community gallery |

### Dashboard
| Method | Endpoint | Description |
|---|---|---|
| GET  | `/api/dashboard/stats` | User statistics |
| PUT  | `/api/dashboard/profile` | Update profile |

---

## 💡 Usage Tips

1. **Be specific with ideas** — "A cyberpunk city where AI robots harvest human memories" generates richer worlds than "sci-fi city"
2. **Mix genres** — Try Fantasy + Political Intrigue + Dark tone for Game of Thrones vibes
3. **Continue stories** — After generating, use "Continue Story" to add chapters
4. **Make worlds public** — Share your creations with the community gallery
5. **Download maps** — SVG maps can be opened in Inkscape or imported into VTTs like Foundry/Roll20

---

## 🐛 Troubleshooting

| Problem | Solution |
|---|---|
| `ModuleNotFoundError: flask` | Run `pip install -r backend/requirements.txt` |
| `401 Unauthorized` on generation | Check your `ANTHROPIC_API_KEY` is set correctly |
| Database errors | Delete `database/storyworld.db` and restart to recreate |
| Port 5000 in use | Set `PORT=5001` or change the port in `backend/app.py` |
| Blank map | Normal if world generation timed out — try regenerating |

---

## 📄 License

MIT License — free for personal and commercial use.

---

*Built with ⚔ artificial magic and real Python.*
