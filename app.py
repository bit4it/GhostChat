from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Dict
import uuid
import json
import os

app = FastAPI(title="GhostChat — Anonymous Messaging")

# ── In-memory stores ───────────────────────────────────────────────────────────
# channels  : { channel_id: { "name": str, "members": set[username] } }
# connected : { username:   { "ws": WebSocket, "channels": set[channel_id] } }
channels:  Dict[str, dict] = {}
connected: Dict[str, dict] = {}


# ── Helpers ────────────────────────────────────────────────────────────────────
async def broadcast(channel_id: str, message: dict, exclude: str | None = None):
    """Send a JSON message to every connected member of a channel."""
    if channel_id not in channels:
        return
    for uname in list(channels[channel_id]["members"]):
        if uname != exclude and uname in connected:
            try:
                await connected[uname]["ws"].send_text(json.dumps(message))
            except Exception:
                pass


def cleanup_user(username: str):
    """Remove a user from all channels and the connected store."""
    if username in connected:
        for cid in list(connected[username].get("channels", set())):
            if cid in channels:
                channels[cid]["members"].discard(username)
        del connected[username]


# ── HTML frontend ──────────────────────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
async def root():
    html_path = os.path.join(os.path.dirname(__file__), "templates", "index.html")
    with open(html_path, "r", encoding="utf-8") as f:
        return f.read()


# ── REST endpoints ─────────────────────────────────────────────────────────────
class ChannelCreate(BaseModel):
    name: str


@app.post("/channels", status_code=201)
def create_channel(body: ChannelCreate):
    # Short 8-char uppercase ID — easy to read and share
    channel_id = str(uuid.uuid4()).replace("-", "")[:8].upper()
    channels[channel_id] = {"name": body.name.strip(), "members": set()}
    return {"channel_id": channel_id, "name": body.name.strip()}


@app.get("/channels/{channel_id}")
def get_channel(channel_id: str):
    cid = channel_id.upper()
    if cid not in channels:
        raise HTTPException(status_code=404, detail="Channel not found")
    data = channels[cid]
    return {
        "channel_id": cid,
        "name": data["name"],
        "online_users": len(data["members"]),
    }


# ── WebSocket endpoint ─────────────────────────────────────────────────────────
# Connect : ws://localhost:8000/ws?username=<name>
#
# Client → Server payloads (JSON):
#   Join    → { "action": "join",    "channel_id": "<id>" }
#   Message → { "action": "message", "channel_id": "<id>", "content": "Hello!" }
#   Leave   → { "action": "leave",   "channel_id": "<id>" }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, username: str):
    # Kick stale connection if the same username reconnects
    if username in connected:
        try:
            await connected[username]["ws"].close(code=4001, reason="Replaced by new connection")
        except Exception:
            pass
        cleanup_user(username)

    await websocket.accept()
    connected[username] = {"ws": websocket, "channels": set()}

    try:
        while True:
            raw = await websocket.receive_text()

            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({"error": "Invalid JSON"}))
                continue

            action     = payload.get("action")
            channel_id = str(payload.get("channel_id", "")).upper()

            # ── Join ──────────────────────────────────────────────────────────
            if action == "join":
                if not channel_id or channel_id not in channels:
                    await websocket.send_text(json.dumps({"error": "Channel not found"}))
                    continue

                # Leave any current channels first
                for old_cid in list(connected[username]["channels"]):
                    if old_cid in channels:
                        channels[old_cid]["members"].discard(username)
                        await broadcast(old_cid, {
                            "event":        "user_left",
                            "username":     username,
                            "online_users": len(channels[old_cid]["members"]),
                        })
                connected[username]["channels"].clear()

                channels[channel_id]["members"].add(username)
                connected[username]["channels"].add(channel_id)

                # Notify existing members
                await broadcast(channel_id, {
                    "event":        "user_joined",
                    "username":     username,
                    "online_users": len(channels[channel_id]["members"]),
                }, exclude=username)

                await websocket.send_text(json.dumps({
                    "event":        "joined",
                    "channel_id":   channel_id,
                    "channel_name": channels[channel_id]["name"],
                    "online_users": len(channels[channel_id]["members"]),
                }))

            # ── Message ───────────────────────────────────────────────────────
            elif action == "message":
                if not channel_id or channel_id not in connected[username]["channels"]:
                    await websocket.send_text(json.dumps({"error": "Join a channel first"}))
                    continue

                content = payload.get("content", "").strip()
                if not content:
                    continue

                msg = {
                    "event":      "message",
                    "channel_id": channel_id,
                    "username":   username,
                    "content":    content,
                }
                # Broadcast to everyone else
                await broadcast(channel_id, msg, exclude=username)
                # Echo back to sender so the message appears in their own UI
                await websocket.send_text(json.dumps({**msg, "self": True}))

            # ── Leave ─────────────────────────────────────────────────────────
            elif action == "leave":
                if channel_id and channel_id in connected[username]["channels"]:
                    channels[channel_id]["members"].discard(username)
                    connected[username]["channels"].discard(channel_id)
                    await broadcast(channel_id, {
                        "event":        "user_left",
                        "username":     username,
                        "online_users": len(channels[channel_id]["members"]),
                    })
                    await websocket.send_text(json.dumps({
                        "event":      "left",
                        "channel_id": channel_id,
                    }))

            # ── Unknown ───────────────────────────────────────────────────────
            else:
                await websocket.send_text(json.dumps({"error": f"Unknown action: '{action}'"}))

    except WebSocketDisconnect:
        # Notify all rooms that this user left
        for cid in list(connected.get(username, {}).get("channels", set())):
            if cid in channels:
                channels[cid]["members"].discard(username)
                try:
                    await broadcast(cid, {
                        "event":        "user_left",
                        "username":     username,
                        "online_users": len(channels[cid]["members"]),
                    })
                except Exception:
                    pass
        cleanup_user(username)
