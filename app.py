# Copyright (C) 2026 Lixiod Technologies

import asyncio
import json
import os
import webbrowser
from typing import Set
from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
import psutil
from mcstatus import JavaServer
from mcrcon import MCRcon

# Load variables from .env file
load_dotenv()

# App Configuration
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 8000))
AUTO_OPEN_BROWSER = os.getenv("AUTO_OPEN_BROWSER", "true").lower() in ("true", "1", "yes")

MC_SERVER_IP = os.getenv("MC_SERVER_IP", "127.0.0.1")
MC_SERVER_PORT = int(os.getenv("MC_SERVER_PORT", 25565))

RCON_ENABLED = os.getenv("RCON_ENABLED", "true").lower() in ("true", "1", "yes")
RCON_PORT = int(os.getenv("RCON_PORT", 25575))
RCON_PASSWORD = os.getenv("RCON_PASSWORD", "")

app = FastAPI(title="DashCraft")

active_connections: Set[WebSocket] = set()

async def get_system_metrics():
    return {
        "cpu": psutil.cpu_percent(interval=None),
        "ram": psutil.virtual_memory().percent,
        "disk": psutil.disk_usage('/').percent
    }

async def get_mc_metrics():
    try:
        server = await JavaServer.async_lookup(f"{MC_SERVER_IP}:{MC_SERVER_PORT}")
        status = await server.async_status()
        
        players_list = []
        if status.players.sample:
            players_list = [p.name for p in status.players.sample]

        return {
            "online": True,
            "players_online": status.players.online,
            "players_max": status.players.max,
            "latency": round(status.latency, 1),
            "version": status.version.name,
            "players_list": players_list
        }
    except Exception:
        return {
            "online": False,
            "players_online": 0,
            "players_max": 0,
            "latency": 0,
            "version": "Unknown",
            "players_list": []
        }

async def broadcast_metrics():
    while True:
        if active_connections:
            sys_data = await get_system_metrics()
            mc_data = await get_mc_metrics()
            
            payload = json.dumps({
                "type": "metrics",
                "system": sys_data,
                "minecraft": mc_data
            })
            
            for connection in list(active_connections):
                try:
                    await connection.send_text(payload)
                except Exception:
                    active_connections.remove(connection)
                    
        await asyncio.sleep(1.5)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(broadcast_metrics())

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.add(websocket)
    try:
        while True:
            data_text = await websocket.receive_text()
            data = json.loads(data_text)
            
            if data.get("action") == "rcon_command":
                if not RCON_ENABLED:
                    await websocket.send_json({
                        "type": "rcon_response",
                        "command": data.get("command", ""),
                        "response": "RCON is disabled in configuration (.env)."
                    })
                    continue

                cmd = data.get("command", "")
                response_text = ""
                try:
                    with MCRcon(MC_SERVER_IP, RCON_PASSWORD, port=RCON_PORT) as mcr:
                        response_text = mcr.command(cmd)
                except Exception as e:
                    response_text = f"RCON Error: {str(e)}"
                
                await websocket.send_json({
                    "type": "rcon_response",
                    "command": cmd,
                    "response": response_text
                })
    except WebSocketDisconnect:
        active_connections.remove(websocket)

@app.get("/", response_class=HTMLResponse)
async def get_dashboard():
    with open("index.html", "r", encoding="utf-8") as f:
        return f.read()

def open_browser_tab():
    """Opens DashCraft automatically in your default web browser."""
    url = f"http://localhost:{PORT}" if HOST in ("0.0.0.0", "127.0.0.1") else f"http://{HOST}:{PORT}"
    print(f"Opening DashCraft in browser at {url}...")
    webbrowser.open(url)

if __name__ == "__main__":
    import uvicorn
    
    # Auto open browser tab after 1.5s delay to let server start up
    if AUTO_OPEN_BROWSER:
        loop = asyncio.get_event_loop()
        loop.call_later(1.5, open_browser_tab)

    uvicorn.run("app:app", host=HOST, port=PORT, reload=False)
