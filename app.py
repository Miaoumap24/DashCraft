import asyncio
import json
from typing import Set
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
import psutil
from mcstatus import JavaServer
from mcrcon import MCRcon

app = FastAPI(title="DashCraft")

# --- CONFIG ---
MC_SERVER_IP = "127.0.0.1"
MC_SERVER_PORT = 25565
RCON_PORT = 25575
RCON_PASSWORD = "rcon_password"  # Edit this password !

# WebSockets
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
        
        # List of Players
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
            "version": "Inconnue",
            "players_list": []
        }

# Realtime Telemetry
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
            # RCON
            data_text = await websocket.receive_text()
            data = json.loads(data_text)
            
            if data.get("action") == "rcon_command":
                cmd = data.get("command", "")
                response_text = ""
                try:
                    with MCRcon(MC_SERVER_IP, RCON_PASSWORD, port=RCON_PORT) as mcr:
                        response_text = mcr.command(cmd)
                except Exception as e:
                    response_text = f"Erreur RCON: {str(e)}"
                
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
