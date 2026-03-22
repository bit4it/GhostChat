<div align="center">

# 👻 GhostChat

**Ephemeral anonymous messaging — no accounts, no history, no trace.**

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![WebSockets](https://img.shields.io/badge/WebSockets-Real--time-6366f1?style=flat-square)](https://websockets.readthedocs.io)
[![License](https://img.shields.io/badge/License-MIT-22d3ee?style=flat-square)](LICENSE)

[Live Demo](#) · [Report Bug](../../issues) · [Request Feature](../../issues)

![GhostChat Preview](https://placehold.co/900x480/07071180/22d3ee?text=GhostChat+Preview&font=montserrat)

</div>

---

## ✨ What is GhostChat?

GhostChat is a **free, real-time anonymous chat app** built with FastAPI and WebSockets. Create a private room in seconds, share the code with friends, and start chatting — no sign-ups, no logs, no data stored anywhere.

When the last person leaves, the room and every message inside it disappear forever.

---

## 🚀 Features

| | Feature | Details |
|---|---|---|
| 👻 | **Fully Anonymous** | No accounts, emails, or phone numbers — ever |
| 🧹 | **Zero Persistence** | Messages live in memory only; close the tab and they're gone |
| ⚡ | **Real-time Messaging** | WebSocket-powered with live join/leave notifications |
| 🔗 | **Shareable Room Codes** | Short 8-character uppercase codes (`A3F8C2D1`) |
| 🎨 | **Modern UI** | Dark-themed SPA with animated landing page, no external JS |
| 📱 | **Responsive** | Works on desktop and mobile |

---

## 🛠️ Tech Stack

- **Backend** — [FastAPI](https://fastapi.tiangolo.com) + [Uvicorn](https://www.uvicorn.org)
- **Real-time** — Native WebSockets via [websockets](https://websockets.readthedocs.io)
- **Frontend** — Vanilla HTML/CSS/JS (zero frameworks, zero dependencies)
- **State** — In-memory only (intentionally no database)

---

## ⚡ Quick Start

**1. Clone the repo**
```bash
git clone https://github.com/your-username/ghostchat.git
cd ghostchat
```

**2. Create a virtual environment & install dependencies**
```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

**3. Run the server**
```bash
uvicorn app:app --reload
```

**4. Open your browser**
```
http://localhost:8000
```

---

## 🗺️ How It Works

```
User A                        Server                        User B
  │                              │                              │
  │── POST /channels ───────────▶│  Create room "A3F8C2D1"     │
  │◀─ { channel_id: A3F8C2D1 } ─│                              │
  │                              │                              │
  │── WS /ws?username=Ghost ────▶│                              │
  │── { action: join, id: ... } ▶│◀─── WS /ws?username=Fox ───│
  │                              │◀─── { action: join, ... } ──│
  │◀── event: user_joined ───────│──── event: user_joined ────▶│
  │                              │                              │
  │── { action: message, ... } ─▶│──── event: message ────────▶│
  │◀── event: message (self) ────│                              │
```

---

## 📡 API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Serves the web app |
| `POST` | `/channels` | Create a new room |
| `GET` | `/channels/{id}` | Check if a room exists |
| `WS` | `/ws?username=<name>` | Open a real-time connection |

### WebSocket Actions

```jsonc
// Join a room
{ "action": "join", "channel_id": "A3F8C2D1" }

// Send a message
{ "action": "message", "channel_id": "A3F8C2D1", "content": "Hello!" }

// Leave a room
{ "action": "leave", "channel_id": "A3F8C2D1" }
```

---

## 📁 Project Structure

```
ghostchat/
├── app.py               # FastAPI app — REST + WebSocket endpoints
├── templates/
│   └── index.html       # Full SPA (landing page + chat UI)
├── requirements.txt
└── README.md
```

---

## 🔒 Privacy by Design

- ❌ No database
- ❌ No message logs
- ❌ No user accounts or sessions
- ❌ No cookies or tracking
- ✅ Everything lives in RAM and is cleared on restart or when users leave

---

## 📄 License

Released under the [MIT License](LICENSE). Free to use, modify, and distribute.

---

<div align="center">
  Made with 👻 and a healthy distrust of surveillance
</div>
